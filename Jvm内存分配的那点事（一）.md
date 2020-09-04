逃逸分析(Escape Analysis)
       逃逸分析的基本行为就是分析对象动态作用域：当一个对象在方法中被定义后，它可能被外部方法所引用，称为方法逃逸。

方法逃逸的几种方式如下：
public class EscapeTest {
    public static Object obj;

    // 给全局变量赋值，发生逃逸
    public void globalVariableEscape() {  
        obj = new Object();
    }

    // 方法返回值，发生逃逸
    public Object methodEscape() {  
        return new Object();
    }

    // 实例引用发生逃逸
    public void instanceEscape() {  
        test(this); 
    }
}
栈上分配
       栈上分配是Java虚拟机提供的一种优化技术，基本思想是:"对于那些线程私有的对象（指的是不可能被其他线程访问的对象），可以将它们直接分配在栈上，而不是分配在堆上"。分配在栈上的好处：可以在函数调用结束后自行销毁，而不需要垃圾回收器的介入，减轻GC压力，从而提升系统的性能。

使用场景
线程私有对象。
受虚拟机栈空间的约束，适用小对象，大对象无法触发虚拟机栈上分配（后面有demo来佐证）。
<<<线程私有变量，大对象虚拟机会分配到TLAB中，TLAB（Thread Local Allocation Buffer）>>>
在栈上分配该对象的内存,当栈帧从Java虚拟机栈中弹出，就自动销毁这个对象。减小垃圾回收器压力。
1、虚拟机内存逻辑图
image.png
2、JVM内存分配源码：
CASE(_new): {
        u2 index = Bytes::get_Java_u2(pc+1);
        ConstantPool* constants = istate->method()->constants();
        // 如果目标Java类已经解析
        if (!constants->tag_at(index).is_unresolved_klass()) {
          // Make sure klass is initialized and doesn't have a finalizer
          Klass* entry = constants->slot_at(index).get_klass();
          assert(entry->is_klass(), "Should be resolved klass");
          Klass* k_entry = (Klass*) entry;
          assert(k_entry->oop_is_instance(), "Should be InstanceKlass");
          InstanceKlass* ik = (InstanceKlass*) k_entry;
          // 如果符合快速分配场景
          if ( ik->is_initialized() && ik->can_be_fastpath_allocated() ) {
            size_t obj_size = ik->size_helper();
            oop result = NULL;
            // If the TLAB isn't pre-zeroed then we'll have to do it
            bool need_zero = !ZeroTLAB;
            if (UseTLAB) {
              result = (oop) THREAD->tlab().allocate(obj_size);
            }
            // 如果TLAB分配失败，就在Eden区分配
            if (result == NULL) {
              need_zero = true;
              // Try allocate in shared eden
        retry:
              // 指针碰撞分配
              HeapWord* compare_to = *Universe::heap()->top_addr();
              HeapWord* new_top = compare_to + obj_size;
              if (new_top <= *Universe::heap()->end_addr()) {
                if (Atomic::cmpxchg_ptr(new_top, Universe::heap()->top_addr(), compare_to) != compare_to) {
                  goto retry;
                }
                result = (oop) compare_to;
              }
            }
            if (result != NULL) {
              // Initialize object (if nonzero size and need) and then the header
              // TLAB区清零
              if (need_zero ) {
                HeapWord* to_zero = (HeapWord*) result + sizeof(oopDesc) / oopSize;
                obj_size -= sizeof(oopDesc) / oopSize;
                if (obj_size > 0 ) {
                  memset(to_zero, 0, obj_size * HeapWordSize);
                }
              }
              if (UseBiasedLocking) {
                result->set_mark(ik->prototype_header());
              } else {
                result->set_mark(markOopDesc::prototype());
              }
              result->set_klass_gap(0);
              result->set_klass(k_entry);
              // 将对象地址压入操作数栈栈顶
              SET_STACK_OBJECT(result, 0);
              // 更新程序计数器PC，取下一条字节码指令，继续处理
              UPDATE_PC_AND_TOS_AND_CONTINUE(3, 1);
            }
          }
        }
        // Slow case allocation
        // 慢分配
        CALL_VM(InterpreterRuntime::_new(THREAD, METHOD->constants(), index),
                handle_exception);
        SET_STACK_OBJECT(THREAD->vm_result(), 0);
        THREAD->set_vm_result(NULL);
        UPDATE_PC_AND_TOS_AND_CONTINUE(3, 1);
      }
代码总体逻辑：JVM再分配内存时，总是优先使用快分配策略，当快分配失败时，才会启用慢分配策略。

1、如果Java类没有被解析过，直接进入慢分配逻辑。
2、快速分配策略，如果没有开启栈上分配或者不符合条件则会进行TLAB分配。
3、快速分配策略，如果TLAB分配失败，则尝试Eden区分配。
4、如果Eden区分配失败，则进入满分配策略。
5、如果对象满足直接进入老年代的条件，那就直接进入老年代分配。
6、快速分配，对于热点代码，如果开启逃逸分析，JVM自会执行栈上分配或者标量替换等优化方案。
3、佐证JVM在某些场景使用栈上分配
设置JVM运行参数：-Xmx10m -Xms10m -XX:+DoEscapeAnalysis -XX:-UseTLAB -XX:+PrintGC

/**
 * @description 开启逃逸模式，关闭线程本地缓存模式（TLAB）（jdk1.8默认开启）
 * -Xmx10m -Xms10m    -XX:+DoEscapeAnalysis  -XX:-UseTLAB  -XX:+PrintGC  
 */
public class AllocationOnStack {

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        for (int index = 0; index < 100000000; index++) {
            allocate();
        }
        long end = System.currentTimeMillis();
        System.out.println((end - start)+" ms");
        Thread.sleep(1000*1000);
        // 看后台堆情况，来佐证关闭逃逸优化后，是走的堆分配。
    }

    public static void allocate() {
        byte[] bytes = new byte[2];
        bytes[0] = 1;
        bytes[1] = 1;
    }
}
运行结果：

[GC (Allocation Failure)  2048K->520K(9728K), 0.0008938 secs]
[GC (Allocation Failure)  2568K->520K(9728K), 0.0006386 secs]
6 ms
jstat -gc pid ，查看内存使用情况：


开启逃逸模式，关闭TLAB
调整JVM运行参数：-Xmx10m -Xms10m -XX:-DoEscapeAnalysis -XX:+UseTLAB -XX:+PrintGC

运行结果：
[GC (Allocation Failure)  2048K->504K(9728K), 0.0013831 secs]
[GC (Allocation Failure)  2552K->512K(9728K), 0.0010576 secs]
[GC (Allocation Failure)  2560K->400K(9728K), 0.0022408 secs]
[GC (Allocation Failure)  2448K->448K(9728K), 0.0006095 secs]
[GC (Allocation Failure)  2496K->416K(9728K), 0.0010540 secs]
[GC (Allocation Failure)  2464K->464K(8704K), 0.0007620 secs]
[GC (Allocation Failure)  1488K->381K(9216K), 0.0007714 secs]
[GC (Allocation Failure)  1405K->381K(9216K), 0.0004409 secs]
[GC (Allocation Failure)  1405K->381K(9216K), 0.0004725 secs]
.......
[GC (Allocation Failure)  2429K->381K(9728K), 0.0008293 secs]
[GC (Allocation Failure)  2429K->381K(9728K), 0.0009006 secs]
[GC (Allocation Failure)  2429K->381K(9728K), 0.0005553 secs]
[GC (Allocation Failure)  2429K->381K(9728K), 0.0005077 secs]
894 ms
jstat -gc pid ，查看内存使用情况：


关闭逃逸模式，开启TLAB模式
调整JVM运行参数：-Xmx10m -Xms10m -XX:-DoEscapeAnalysis -XX:-UseTLAB -XX:+PrintGC

运行结果：
[GC (Allocation Failure)  2048K->472K(9728K), 0.0007073 secs]
[GC (Allocation Failure)  2520K->528K(9728K), 0.0009216 secs]
[GC (Allocation Failure)  2576K->504K(9728K), 0.0005897 secs]
[GC (Allocation Failure)  2551K->424K(9728K), 0.0005780 secs]
[GC (Allocation Failure)  2472K->440K(9728K), 0.0006923 secs]
[GC (Allocation Failure)  2488K->456K(8704K), 0.0006277 secs]
[GC (Allocation Failure)  1480K->389K(9216K), 0.0005560 secs]
.......
[GC (Allocation Failure)  2437K->389K(9728K), 0.0003227 secs]
[GC (Allocation Failure)  2437K->389K(9728K), 0.0004264 secs]
[GC (Allocation Failure)  2437K->389K(9728K), 0.0004396 secs]
[GC (Allocation Failure)  2437K->389K(9728K), 0.0002773 secs]
[GC (Allocation Failure)  2437K->389K(9728K), 0.0002766 secs]
1718 ms
关闭逃逸，关闭TLAB
运行结果对比：
1、运行耗时（开启逃逸 VS关闭逃逸(开启TLAB)VS关闭逃逸(关闭TLAB))：
     6ms VS 894ms VS 1718ms
2、虚拟机内存&回收♻️（开启逃逸VS关闭逃逸）：
堆内存&YoungGC回收♻️对比
总结：
启动参数	JVM内存分配模式	Eden区	YoungGC	耗时
-XX:+DoEscapeAnalysis（开逃逸分析）-XX:+UseTLAB （开启TLAB）	虚拟机栈上分配模式(小对象)	较少使用	较少使用	很低
-XX:-DoEscapeAnalysis（关闭逃逸分析）-XX:+UseTLAB（开启TLAB）	TLAB区分配模式	大量使用	大量使用	较高
-XX:-DoEscapeAnalysis（关闭逃逸分析）-XX:-UseTLAB（关闭TLAB）	Eden区分配模式	大量使用	大量使用	特别高
整个对比会很疑惑？
     -XX:-DoEscapeAnalysis -XX:-UseTLAB VS -XX:-DoEscapeAnalysis -XX:+UseTLAB 耗时为何相差这么多？
     原因就在TLAB分配与Eden区分配存在差异，TLAB（Thread Local Allocation Buffer）是在共享堆上安全分配，没有指针碰撞！<<<<<<传送门

调整分配空间大小：
/**
 * -Xmx10m -Xms10m    -XX:-DoEscapeAnalysis -XX:+UseTLAB  -XX:+PrintCommandLineFlags -XX:+PrintGC 
 */
public class AllocationOnStack {

    private static final int _1B =  65;

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        for (int index = 0; index < 100000000; index++) {
            allocateBigSpace();
        }
        long end = System.currentTimeMillis();
        System.out.println(end - start);
        Thread.sleep(1000*1000);
        // 看后台堆情况，来佐证关闭逃逸优化后，是走的堆分配。
    }

    public static void allocate() {
        byte[] bytes = new byte[2];
        bytes[0] = 1;
        bytes[1] = 1;
    }
    public static void allocateBigSpace() {
        byte[] allocation1;
        allocation1 = new byte[1 * _1B];
      

      
    }

}
运行结果:
-XX:+DoEscapeAnalysis -XX:InitialHeapSize=5242880 -XX:MaxHeapSize=5242880 -XX:+PrintCommandLineFlags -XX:+PrintGC -XX:+UseCompressedClassPointers -XX:+UseCompressedOops -XX:+UseParallelGC -XX:-UseTLAB 
[GC (Allocation Failure)  1023K->516K(5632K), 0.0028410 secs]
[GC (Allocation Failure)  1540K->578K(5632K), 0.0023265 secs]
........
[GC (Allocation Failure)  2466K->1442K(5632K), 0.0013395 secs]
[GC (Allocation Failure)  2466K->1442K(5632K), 0.0004367 secs]
8925
调整启动参数： -XX:+DoEscapeAnalysis -XX:-UseTLAB

运行结果:
-XX:+DoEscapeAnalysis -XX:InitialHeapSize=5242880 -XX:MaxHeapSize=5242880 -XX:+PrintCommandLineFlags -XX:+PrintGC -XX:+UseCompressedClassPointers -XX:+UseCompressedOops -XX:+UseParallelGC -XX:-UseTLAB 
[GC (Allocation Failure)  1023K->516K(5632K), 0.0028410 secs]
[GC (Allocation Failure)  1540K->578K(5632K), 0.0023265 secs]
........
[GC (Allocation Failure)  2466K->1442K(5632K), 0.0013395 secs]
[GC (Allocation Failure)  2466K->1442K(5632K), 0.0004367 secs]
8925
经过对比得出结论：
分配内存为>64byte == -XX:-UseTLAB

经过多次测试发现当_1B=64b时效率还是非常高，一旦大于64b就会急剧下降。所以推断出64byte是JVM选择是TLAB分配 OR Eden区分配的临界值。
