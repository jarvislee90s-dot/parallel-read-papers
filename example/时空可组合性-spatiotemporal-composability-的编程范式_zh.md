# 时空可组合性（Spatiotemporal Composability）的编程范式

石一帆（Yifan Shi）<sup>1,2</sup>、张伟（Wei Zhang）<sup>1</sup>、崔天翼（Tianyi Cui）<sup>2</sup>

<sup>1</sup>北京大学（Peking University）<sup>2</sup>深度求索（DeepSeek-AI）

## 摘要（Abstract）

现代软件——从插件系统到自我演化的智能体框架（agent harnesses）——越来越需要动态组合（dynamic composition），然而其形式化基础仍不成熟。我们识别出该问题的两个正交维度：时间可组合性（temporal composability），即组件被移除时其副作用能够被完全逆转的能力；以及空间可组合性（spatial composability），即声明并响应式地管理组件间依赖的能力。我们通过把经典的效应（effect）与余效应（coeffect）概念提升为运行时机制来应对这两个维度。具体而言，我们形式化了可逆效应（revertible effects）：每个上下文变换都携带一个由运行时跟踪的逆。我们形式化了响应式余效应（reactive coeffects）：上下文的每次变化都根据组件的余效应规范通知该组件。我们把效应上下文与余效应上下文统一为单一的上下文类型，这构成了一种编程范式。此后，我们把这些机制组合成组件的概念，并给出一个动态组合演算，其元理论把时空可组合性从单个组件推广到整个交错组件系统。我们在 Cordis 中实现了这些思想——一个时空可组合性的元框架，提供带效应跟踪与余效应解析的核心库，以及带配置对账（configuration reconciliation）与热模块替换（hot module replacement）的声明式组件加载器。

## 1. 引言（Introduction）

组合（composition）——用较简单的部分组装复杂系统——是软件工程的基本原则 [1]。传统上，组合是静态的：函数调用、模块导入和类继承在编译时解析，并在整个执行期间保持不变。然而，现代软件越来越需要动态组合，即组件在运行时被加载、卸载和重新配置。插件架构 [2] 和自演化智能体框架都要求系统能安全地即时添加和移除功能，但当前实践退而求其次地依赖粗粒度机制 [3]，只能通过重启来重新配置，从而丢弃运行时状态。尽管动态组合的实践重要性日益增长，其理论基础仍然薄弱，与静态组合丰富的形式化框架相比相形见绌。

## 1.1. 可组合性的维度（Dimensions of Composability）

为刻画动态组合的需求，我们在组合已得到充分研究的代数性质之外，识别出两个正交维度：

• 时间可组合性关注时间维度：在移除一个组件时，该组件对共享环境所做的修改必须被完全且安全地逆转。这要求跟踪组件执行的每一次资源分配、事件注册和状态变更，并保证在移除时有序回收。

• 空间可组合性关注空间维度：组件必须能够以结构化且可验证的方式声明、发现和解析彼此之间的依赖。这要求管理依赖拓扑，并针对依赖变化协调组件生命周期。

在静态设定下，时间可组合性归结为词法作用域（如 RAII [4]、括号模式 [5]），空间可组合性归结为模块导入解析 [6]。在动态设定下，组件在运行时到达和离开，两个维度都变得显著更困难：时间可组合性必须处理生命周期长、作用域不受词法约束的有状态效应；空间可组合性必须处理在执行期间出现、消失或改变身份的依赖。

## 1.2. 动机示例（Motivating Examples）

## 1.2.1. 插件系统（Plugin Systems）

插件系统是动态组合的典型实例。我们用 Visual Studio Code（VSCode）——使用最广泛的可扩展 IDE 之一——作为代表性示例。

时间上的局限。VSCode 在称为扩展宿主（extension host）的共享进程中运行所有扩展。虽然扩展可以动态安装，但这个宿主没有提供在运行时卸载单个扩展代码的机制。一旦扩展的 activate 函数执行完毕，禁用或卸载它就需要重启整个宿主，影响所有已加载的扩展。纯声明式扩展（如主题、按键绑定和代码片段）不携带代码，可以自由移除。然而在按安装量排名的前 100 个扩展中，87 个包含可执行代码<sup>1</sup>，因此在移除时需要这样的重启。虽然 VSCode 提供了 deactivate 钩子，但它只是在宿主进程终止期间作为优雅关闭回调，因此不能实现实时移除。此外，该钩子把效应处置与效应创建（在 activate 中）分离开来，违背了关注点局部性，使完全清理难以验证。

空间上的局限。VSCode 确实提供了 extensionDependencies 来声明扩展之间的依赖，但它很少被使用：在按安装量排名的前 100 个扩展中，只有 7 个对非内置扩展声明了 extensionDependencies。<sup>1</sup> 这种稀缺反映了扩展 API 的形态，它暴露的是固定的、表面级的扩展点（如命令、视图和语言特性）。扩展通过这些点向宿主贡献能力，而不是相互依赖，因此扩展间的依赖很少出现。此外，VSCode 的扩展间交互机制不提供任何结构契约：它通过 vscode.extensions.getExtension(...).exports 向其他扩展暴露功能，但返回的值是无类型的（默认 any），因此依赖方无法依赖被检查的接口。简而言之，VSCode 把扩展引向一组固定的宿主提供的扩展点，并且不为它们之间的相互依赖提供安全、结构化的方式。

这两个局限并非 VSCode 独有；它们在各类插件系统中普遍存在 [2, 7]，只是程度不同。

## 1.2.2. 自我演化的智能体框架（Self-Evolving Agent Harnesses）

现代 AI 智能体依赖运行时智能体框架 [8–10]。这些系统可能组合多样化的工具套件 [11] 和执行环境，管理权限与沙箱，维护会话状态与持久化，提供上下文管理与记忆系统 [12]，编排子智能体与多智能体工作流 [13]，并向用户和自动化暴露接口。未来的框架可能在持续服务请求的同时，生成并部署对其自身组件的修改。模型合成的可复用工具为组件级自我修改提供了一个较窄的先驱 [14]。每一次这样的修改本身都是动态组合的一个实例。

由于这些修改连续发生，且几乎没有或完全没有人工监督，动态可组合性变得不可或缺。没有时间可组合性，每一次自我修改都迫使完全重启，丢弃所有进程内累积的状态；在这样的频率下，累积的不可用时间变得可观，进行中的任务被反复中断；更糟的是，一个有缺陷的自我修改可能禁用用于恢复的进程本身。没有空间可组合性，每个模块都必须自己检测并适应它所依赖模块的变化——这些模块出现、消失或改变身份——且只能通过临时手段进行；更糟的是，天真的代码替换策略可能静默破坏依赖方，或引入只有在重载时才暴露的循环依赖。

## 1.2.3. 粗粒度变通方案（The Coarse-Grained Workaround）

动态组合在形式上受到有限关注的一个原因是，操作系统和容器编排器已经提供了粗粒度的替代品。操作系统以进程为粒度提供时间可组合性；容器编排器 [3] 以服务为粒度提供空间可组合性。在实践中，大多数软件通过退守这些粗粒度机制来容忍细粒度可组合性的缺失：行为异常的模块通过重启进程来处理，服务依赖由容器编排器管理。

然而，这种变通方案代价高昂。在时间上，每次重启都会丢弃所有进程内累积的状态（如缓存、连接、部分计算），重建它需要数秒到数分钟 [15]；期间维持可用性需要冗余副本，为弥补无法恢复单个组件的缺陷而付出资源开销。在空间上，容器级编排无法表达共享同一地址空间的组件之间的依赖，并为本可以成为本地函数调用的交互引入网络开销。这两种机制都在进程和容器的边界处运作，而现代系统越来越在更细的层次上组合。这种粒度不匹配要求一种组合抽象，在与组件本身相同的层次上管理效应和依赖。

## 1.3. 贡献（Contributions）

动态组合的两个维度分别关注计算如何修改其环境，以及如何依赖其环境。这两个方向正是效应系统 [16, 17] 和余效应系统 [18, 19] 所形式化的：效应提供了推理环境修改的形式化词汇，余效应提供了推理环境需求的词汇。然而，现有表述把推理限制在词法固定作用域上的编译时分析，不扩展到组件在运行时到达和离开的动态场景。通过把效应提升为可逆的运行时模型，把余效应提升为响应式的依赖解析机制，我们为动态组合获得了一个统一的形式化基础——一个与语言无关、适用于任何需要动态组合的软件架构的基础。我们做出以下贡献：

1. 我们形式化了可逆效应（第 3.1 节）：每个上下文变换都携带一个由运行时跟踪的显式逆，跟踪和恢复都保持组合性，因此在组件移除时上下文被恢复。这建立了局部时间可组合性。

2. 我们形式化了响应式余效应（第 3.2 节）：组件把它所需的余效应声明为一个规范，上下文的每次变化都根据该规范把状态分类为激活、停用或中性，并通知该组件。这建立了局部空间可组合性。

3. 我们把效应上下文与余效应上下文统一为单一上下文类型（第 3.3 节），其中余效应上的观测等价为效应提供独立性，构成时空可组合性的编程范式。

4. 我们给出了动态组合演算（第 4 节），它把这两种机制组合为组件的概念，并为其生命周期配备操作语义。其元理论把时空可组合性从单个组件推广到整个交错组件系统。

5. 我们在 Cordis（第 5 节）中实现了这些思想——一个时空可组合性的元框架，提供实现形式模型的核心库（带效应跟踪与余效应解析），以及带配置对账与热模块替换的声明式组件加载器。

## 2. 预备知识（Preliminaries）

本节简要概述效应与余效应系统——支撑我们工作的两大理论支柱。我们假定读者熟悉基本的类型论与范畴论；这里的目标是固定记号并引入第 3 节将作为运行时机制操作化的关键抽象。

## 2.1. 效应（Effects）

在简单类型 λ 演算（STLC）[20, 21] 中，类型判断 $\Gamma \vdash t : T$ 陈述项 t 在上下文 Γ 下具有类型 $_ T$。效应系统精化该类型，以描述计算可能产生哪些副作用，产生如下形式的判断

$$
\Gamma \vdash t: T _ {\mathrm{effect}}\tag{1}
$$

这里，结果类型被注解以效应代数的元素，它描述计算可能产生哪些副作用，从而能够对状态性计算进行组合式推理。这种方法起源于 Lucassen 和 Giford [22]，他们引入了一种分类类型系统，区分类型、效应和区域，以发现并行程序中的调度约束。

单子效应。Moggi [16] 首先通过单子对计算效应进行了范畴论建模；Wadler [23] 在 Haskell 中推广了这种方法。范畴 C 上的一个单子 $( T , \eta , \mu )$ 把一次有效应计算封装为 $T ( A )$ 类型的值，其中 $\eta : A  T ( A )$ 提升纯值，$\mu : T ( T ( A ) ) \to T ( A )$ 对嵌套计算进行排序。经典实例包括 Maybe 单子（表示部分性）、State 单子（表示可变状态）和 IO 单子（表示外部交互）。

代数效应。Plotkin 和 Power [17, 24] 表明代数运算决定单子，建立了效应接口与其实现解耦的框架。效应签名 Σ 声明一组运算 $( \mathrm { e . g . , g e t : } ( ) \to S , \mathrm { p u t : } S \to ( )$ 用于状态）；程序自由地调用运算，而不承诺特定的解释。Plotkin 和 Pretnar [25] 随后引入了效应处理器，它通过提供续延语义来解释运算：

$$
\text { handle } e \text { with } \{\mathrm{op} (v, \kappa) \mapsto \dots \}\tag{2}
$$

处理器接收运算参数 x 和限定续延（delimited continuation）$\kappa ,$ 它可以调用零次、一次或多次，从而在统一框架内支持异常、协程和非确定性 [26]。Koka [27, 28]、Ef [29] 和 OCaml 5 [30] 等语言以不同的设计取舍采纳了代数效应。

## 2.2. 余效应（Coeffects）

与效应相对偶，余效应系统 [18, 31] 丰富的是上下文而非类型，产生如下形式的判断

$$
\Gamma_ {\mathrm{coeffect}} \vdash t: T\tag{3}
$$

这里，上下文被注解以余效应代数的元素，它描述计算从环境需要什么，例如要访问的资源、要持有的权限或要依赖的服务。效应建模程序对世界的影响，而余效应建模世界对程序的约束。

余单子余效应。用余单子结构化上下文相关计算的想法最初由 Uustalu 和 Vene [32] 提出，他们提出对称（半）幺半余单子，作为 Moggi's 单子效应框架的对偶，捕获数据流和属性求值等概念。Petricek 等人 [18] 在此基础之上提出余效应作为上下文依赖的统一静态分析。一个余单子 $( D , \varepsilon , \delta )$ 捕获上下文相关计算：$\varepsilon : D ( A ) \to A$ 从上下文提取当前值，$\delta : D ( A )  D ( D ( A ) )$ 为嵌套访问复制上下文。Environment 余单子 $D ( X ) = E \times X$ 建模对固定环境 $E ;$ 的依赖；Stream 余单子 $D ( X ) =$ $\mathbb { N } \to X$ 建模对时序数据的依赖。

分次余效应。为进行更精细的跟踪，分次余效应系统使用预序半环 $\pmb { S } = ( S , \pmb { \Sigma } , + , \times , 0 , 1 )$ 作为余效应代数 [33]，这一纪律后来被 Gaboardi 等人 [19] 与分次效应统一。S 的元素注解每个变量绑定以量化其使用：0 表示未使用，1 表示线性使用，ω 表示有界使用，$\infty$ 表示无限制使用。半环运算按顺序 $( \times )$ 和并行 (+) 组合余效应，从而在统一的代数框架 [37] 内实现精确的资源跟踪、敏感度分析 [34] 和信息流控制 [35, 36]。

## 2.3. 与动态组合的关系（Relationship to Dynamic Composability）

效应与余效应系统沿两个互补方向组织关于计算的推理：效应描述计算如何修改其环境，而余效应描述计算如何依赖其环境。这两个方向对应第 1 节识别的动态组合的两个维度：

• 时间可组合性要求组件对共享环境的修改在卸载时可逆。相关的效应是有状态的那些，它们持久地变换该环境；撤销这样的变换要求它容许一个逆。

• 空间可组合性要求组件间依赖被声明并响应式地管理。这样的依赖正是余效应所捕获的，而管理它们相当于把每个依赖对环境中提供的东西进行解析。

然而，经典效应与余效应系统是静态工具：效应在词法固定作用域内被跟踪，由编译时处理器清结（discharge）；余效应注解针对执行前确定的上下文进行验证。相比之下，动态组合要求这些保证对在运行时到达和离开的组件成立，而对持续演化的上下文成立。没有任何固定词法作用域可以限定部署后加载的插件；没有任何编译时上下文可以预见运行时配置中涌现的依赖。

这促使视角的转变：与其用更多注解扩展静态类型系统，我们把效应和余效应的概念结构具体化（reify），使运行时能够直接对它们操作，从而在动态中建立这些系统在静态中提供的保证。

## 3. 可逆效应与响应式余效应（Revertible Effects and Reactive Coeffects）

本节把第 2 节引入的效应与余效应概念提升为运行时机制，构建动态组合的理论。核心思想是把携带效应和余效应的类型上下文转变为上下文类型（context types）——把上下文具体化为第一类实体的、可在运行时操作的类型。对效应类型，我们把它建模为带逆的上下文变换，实现局部时间可组合性。对余效应上下文，我们把它建模为携带依赖信息的类型，实现局部空间可组合性。随后余效应上的观测等价为效应提供独立性。同时携带效应和余效应的统一上下文自身构成一种编程范式。

## 3.1. 可逆效应（Revertible Effects）

时间可组合性是在运行时加载和卸载组件，使得卸载时共享环境恢复到组合前的状态的能力。这要求组件对环境所做的每次修改都可跟踪、可恢复。因此我们把效应建模为类型 $\Gamma  \Gamma \times ( \Gamma  \Gamma )$ 的函数：应用于当前上下文时，它产生修改后的上下文以及一个显式逆。提供该逆使效应可被逆转，把它交给运行时使效应可被跟踪。我们称这样的效应为可逆的：在执行期间跟踪并组合这些逆，完整的环境恢复就成为结构性保证。

## 3.1.1. 效应上下文（Effect Context）

给定任意非纯函数 $f _ { \mathrm { i m p u r e } } : X  Y .$，我们把它变换为纯形式 $f : \Gamma \times X \to \Gamma \times$ $Y ,$ 其中 Γ 是上下文，所有可能的副作用都可以表示为对 Γ 的变换。对任意固定输入 $x : X ,$，诱导映射 $\gamma \mapsto \operatorname { p r } _ { 1 } ( f ( \gamma , x ) )$ ) 独立于返回值捕获 f 的副作用。因此 Γ 上的效应位于变换 Γ → Γ 的幺半群中（在复合 $^ \circ$ 下），其中每个幺半群公理都可以直接读作效应的一种性质：

• 封闭性（Closure）：两个效应的顺序复合仍是一个效应；

• 结合性（Associativity）：复合效应的结果与其括号方式无关；

• 单位元（Identity）：${ \mathrm { i d } } _ { \Gamma } ,$ 即 Γ 上的恒等函数，作为复合的单位。

为建模可被撤销的效应，我们把每个变换 $f$ 与撤销 $f$ 的另一个变换 g 配对，并称 g 为 $f$ 的左逆，在本文中简称为逆。撤销是单侧的：逆被要求满足的是 $g \circ f$ 而绝非 $f \circ g$ 。变换对携带它们自己的乘法：

定义 1. 定义上下文变换对的扭转复合（twisted composition）为

$$
\left(f _ {1}, g _ {1}\right) \circ \left(f _ {2}, g _ {2}\right) := \left(f _ {1} \circ f _ {2}, g _ {2} \circ g _ {1}\right)\tag{4}
$$

与 ∘ 本身一样，左操作数在右操作数之后作用，而逆以相反的顺序累积。它使 $( \Gamma  \Gamma ) \times ( \Gamma  \Gamma )$ 成为以 $( \mathrm { i d } _ { \Gamma } , \mathrm { i d } _ { \Gamma } )$ 为单位的幺半群，即变换幺半群与其对偶的积，我们称之为 Γ 上的扭转复合幺半群 $\mathfrak { T } _ { \Gamma }$。

为在上下文内部跟踪效应，我们引入以下定义：

定义 2. 给定上下文 Γ，定义其效应上下文为：

$$
\partial \Gamma := \Gamma \times (\Gamma \to \Gamma)\tag{5}
$$

它可以理解为二元组 $( \gamma , \varphi )$ ，其中：

• γ : Γ 是当前上下文状态；

$\varphi : \Gamma \to \Gamma$ 是累加器（accumulator），即迄今为止所执行效应之逆的复合，是把上下文恢复到初始状态的函数。

特别地，初始效应上下文可以表示为 $( \gamma _ { 0 } , \mathrm { i d } _ { \Gamma } )$

我们还写 $\partial ^ { 2 } \Gamma = \partial \Gamma \times ( \partial \Gamma \to \partial \Gamma )$ ，以此类推向上攀升。

鉴于累加器 $\varphi ,$ 的存在，对 $\partial \Gamma$ 执行的所有效应都可被跟踪和恢复。我们现在给出跟踪与恢复的具体构造。

定义 3. 在上下文函数对上定义变换 track：

$$
\begin{array}{r c l r c l r c l} \mathrm{track} _ {\Gamma} & : & (\Gamma \to \Gamma) \times (\Gamma \to \Gamma) & \to & \partial \Gamma & \to & \partial \Gamma \\ \mathrm{track} _ {\Gamma} & = & (f, g) & \mapsto & (\gamma , \varphi) & \mapsto & (f (\gamma), \varphi \circ g) \end{array}\tag{6}
$$

该变换把一个正向函数 f 连同候选逆 g 转换为效应上下文 ∂Γ 上的一个变换。把 $\operatorname { t r a c k } _ { \Gamma } ( f , g )$ 应用于状态 $( \gamma , \varphi )$ 用 f 变换 $\gamma$ 并把逆 g 复合到 $\varphi ,$ 上，从而在上下文中跟踪 f 的效应。

定理 4. 对每个 $( f , g ) \in ( \Gamma \to \Gamma ) \times ( \Gamma \to \Gamma )$ 下图可交换，即

$$
\mathrm{pr} _ {1} \circ \operatorname{track} _ {\Gamma} (f, g) = f \circ \mathrm{pr} _ {1}\tag{7}
$$

![](images/0de223e0a5a4e1797f6853ea767a9ac4b7af12df5ccaad388281389857daefa3.jpg)

证明. 对所有 $( \gamma , \varphi ) \in \partial \Gamma$

$$
\begin{array}{c} (\mathrm{pr} _ {1} \circ \mathrm{track} _ {\Gamma} (f, g)) (\gamma , \varphi) = \mathrm{pr} _ {1} (f (\gamma), \varphi \circ g) \\ = f (\gamma) \\ = (f \circ \mathrm{pr} _ {1}) (\gamma , \varphi) \end{array}
$$

定理 5. track 是从 $\mathfrak { T } _ { \Gamma }$ 到 $\partial \Gamma  \partial \Gamma$ 的幺半群同态。即，

1. track $\hat { \varepsilon } _ { \Gamma } ( \mathrm { i d } _ { \Gamma } , \mathrm { i d } _ { \Gamma } ) = \mathrm { i d } _ { \partial \Gamma } ;$

2. 对所有 $( f _ { 1 } , g _ { 1 } ) , ( f _ { 2 } , g _ { 2 } ) \in \mathfrak { T } _ { \Gamma } ,$

$$
\operatorname{track} _ {\Gamma} \left(\left(f _ {1}, g _ {1}\right) \circ \left(f _ {2}, g _ {2}\right)\right) = \operatorname{track} _ {\Gamma} \left(f _ {1}, g _ {1}\right) \circ \operatorname{track} _ {\Gamma} \left(f _ {2}, g _ {2}\right)\tag{8}
$$

证明.

1. 单位元被送到单位元，因为 track $\langle \mathrm { i d } _ { \Gamma } , \mathrm { i d } _ { \Gamma } ) ( \gamma , \varphi ) = ( \gamma , \varphi \circ \mathrm { i d } _ { \Gamma } ) = ( \gamma , \varphi )$

2. 对乘法，取任意 $( \gamma , \varphi ) \in \partial \Gamma$

$$
\begin{array}{r l} & (\mathrm{track} _ {\Gamma} (f _ {1}, g _ {1}) \circ \mathrm{track} _ {\Gamma} (f _ {2}, g _ {2})) (\gamma , \varphi) = \mathrm{track} _ {\Gamma} (f _ {1}, g _ {1}) (f _ {2} (\gamma), \varphi \circ g _ {2}) \\ & \qquad = (f _ {1} (f _ {2} (\gamma)), \varphi \circ g _ {2} \circ g _ {1}) \\ & \qquad = \mathrm{track} _ {\Gamma} (f _ {1} \circ f _ {2}, g _ {2} \circ g _ {1}) (\gamma , \varphi) \end{array}
$$

定义 6. 在 $\partial \Gamma$ 上定义变换 recover：

$$
\begin{array}{r c l r c l} \mathrm{recover} _ {\Gamma} & : & \partial \Gamma & \to & \partial \Gamma \\ \mathrm{recover} _ {\Gamma} & = & (\gamma , \varphi) & \mapsto & (\varphi (\gamma), \mathrm{id} _ {\Gamma}) \end{array}\tag{9}
$$

该变换把恢复函数 $\varphi$ 应用于当前状态 $\gamma$ 并把 $\varphi$ 重置为恒等。下图说明在一系列效应 track $( f _ { 1 } , g _ { 1 } ) , \cdots$ ，track $( f _ { n } , g _ { n } )$ 应用于 ∂Γ 后，recover 如何把上下文恢复到其初始状态：

$$
\begin{array}{c} \Gamma \xrightarrow {f _ {1}} \Gamma \xrightarrow {} \Gamma \xrightarrow {} \Gamma \\ \Bigg | \Bigg | \text { track } \\ \partial \Gamma \xrightarrow {f _ {1} ^ {\prime}} \partial \Gamma \xrightarrow {} \partial \Gamma \xrightarrow {} \partial \Gamma \\ \Bigg | \Bigg | \text { track } \\ \Bigg | \Bigg | \text { track } \\ \Bigg | \Bigg | \text { recover } \\ \end{array}
$$

该图表明被跟踪的效应随后跟一个 recover 会把初始效应上下文带回到其自身。每个跟踪步骤所保持的是恢复本身的结果，无论从什么状态取之：

定理 7. 对每个 $( \gamma , \varphi ) \in \partial \Gamma$ 和每个满足 $\begin{array} { r } { g ( f ( \gamma ) ) = \gamma , } \end{array}$ 的对 $( f , g )$

$$
\mathrm{recover} _ {\Gamma} (\mathrm{track} _ {\Gamma} (f, g) (\gamma , \varphi)) = \mathrm{recover} _ {\Gamma} (\gamma , \varphi)\tag{10}
$$

证明.

$$
\begin{array}{r l} & {\mathrm{recover} _ {\Gamma} (\mathrm{track} _ {\Gamma} (f, g) (\gamma , \varphi)) = \mathrm{recover} _ {\Gamma} (f (\gamma), \varphi \circ g)} \\ & {\qquad = (\varphi (g (f (\gamma))), \mathrm{id} _ {\Gamma})} \\ & {\qquad = (\varphi (\gamma), \mathrm{id} _ {\Gamma}) = \mathrm{recover} _ {\Gamma} (\gamma , \varphi)} \end{array}
$$

一列对无需单独论证。设 $( f _ { 1 } , g _ { 1 } ) , \cdots , ( f _ { n } , g _ { n } )$ 从 $( \gamma , \varphi )$ 按顺序应用，并写 $\delta _ { 0 } = \gamma$ 且 $\bar { \delta _ { i } \ : = \ : f _ { i } ( \delta _ { i - 1 } ) }$ )。由定理 5 复合 track $\digamma ( f _ { n } , g _ { n } )$ ∘ ⋯ ∘ track $\cdot ( f _ { 1 } , g _ { 1 } )$ 是扭转复合 $( f _ { n } \circ \cdots \circ f _ { 1 } , g _ { 1 } \circ \cdots \circ g _ { n } )$ 的 track，若对每个 i 有 $g _ { i } ( \delta _ { i } ) = \delta _ { i - 1 }$ 则 $( g _ { 1 } \circ \cdots \circ g _ { n } ) ( \delta _ { n } ) = \delta _ { 0 } = \gamma$ 。因此该对在 $\gamma$ 处满足定理 $7$ 的假设，应用一次该定理即得

$$
\operatorname{recover} _ {\Gamma} \left(\left(\operatorname{track} _ {\Gamma} \left(f _ {n}, g _ {n}\right) \circ \dots \circ \operatorname{track} _ {\Gamma} \left(f _ {1}, g _ {1}\right)\right) (\gamma , \varphi)\right) = \operatorname{recover} _ {\Gamma} (\gamma , \varphi)\tag{11}
$$

取 $( \gamma , \varphi ) = ( \gamma _ { 0 } , \mathrm { i d } _ { \Gamma } )$ ，恢复把每个以此方式达到的状态带回到 $( \gamma _ { 0 } , \mathrm { i d } _ { \Gamma } )$ 。满足 $g \circ f = \operatorname { i d } _ { \Gamma }$ 的对在任意状态满足该假设。

恢复通过量 $\varphi ( \gamma )$ 读取一个状态，我们把 $\varphi ( \gamma ) = \gamma _ { 0 }$ 称为 $\partial \Gamma$ 中状态的可靠性不变量（soundness invariant）。

## 3.1.2. 可逆效应函数（Revertible Effect Functions）

上一节的 track/recover 模型把逆视为先验给定的：$\operatorname { t r a c k } _ { \Gamma } ( f , g )$ 在看到任何上下文状态之前就固定了 $g$，因此一个 g 必须服务于效应所应用的每个状态。然而在实践中，每个效应的逆并非先验已知：它必须在效应应用点由调用者提供。此外，recover 是全有或全无的：它不能选择性地撤销一个效应而保留其他效应。为处理这两个问题，我们在输入侧和输出侧都增强模型：

1. 在输入侧，我们不仅变换 Γ，还同时返回一个逆函数，使逆在效应被应用之处提供：$\Gamma \to \Gamma \times ( \Gamma \to \Gamma ) , \mathrm { i . e . } , \Gamma \to \partial \Gamma .$；

2. 在输出侧，我们不仅变换 ∂Γ，还同时返回一个逆函数，使一个效应可以被撤销而其他效应被保留：$\partial \Gamma \to \partial \Gamma \times ( \partial \Gamma \to \partial \Gamma ) , \mathrm { i . e . , } \partial \Gamma \to \partial ^ { 2 } \Gamma$

这种增强在输入和输出之间保持结构一致性，因此我们仍然可以定义维护 track 数学性质的相应理论。得到的类型是效应函数 $\mathfrak { E } _ { \Gamma }$ 及其带见证的精化 ${ \mathfrak { E } } _ { \Gamma } ^ { * }$：

定义 8. 定义效应函数 $\mathfrak { E } _ { \Gamma }$ 和带见证的效应函数 ${ \mathfrak { E } } _ { \Gamma } ^ { * }$ 为：

$$
\begin{array}{r l} & {\mathfrak {E} _ {\Gamma} := \Gamma \to \Gamma \times (\Gamma \to \Gamma)} \\ & {\mathfrak {E} _ {\Gamma} ^ {*} := (e: \Gamma \to \Gamma \times (\Gamma \to \Gamma))} \\ & {\qquad \times ((\gamma : \Gamma) \to ((\delta : \Gamma) \times (g: \Gamma \to \Gamma) \times ((\delta , g) = e (\gamma) \to g (\delta) = \gamma)))} \end{array}\tag{12}
$$

其中 $e ( \gamma )$ 产生二元组 $( \delta , g )$ 表示：

$\delta : \Gamma$ 是新的上下文；

$g : \Gamma \to \Gamma$ 是当前效应的逆函数。

${ \mathfrak { E } } _ { \Gamma } ^ { * }$ 的元素按状态选择其逆，约束 $g ( \delta ) = \gamma$ 把该选择约束为在效应被应用之处逆转效应，而在别处对 g 不加约束。满足 $g \circ f = \operatorname { i d } _ { \Gamma }$ 的单一 $g$ 在每个状态同时满足该约束，并通过 $( f , g ) \mapsto \gamma \mapsto ( f ( \gamma ) , g )$ 诱导出 ${ \mathfrak { E } } _ { \Gamma } ^ { * }$ 的一个元素，定理 11 将表明这是一个同态。该约束可以可视化为如下交换图，确保逆 g 确实在 f 被应用的状态处逆转该变换：

![](images/cdc9de28649b1c51171c71052d5218755b00d8a4a37196154a79f8495ffa0ace.jpg)

由于效应函数 $\mathfrak { E } _ { \Gamma }$ 不再是上下文上的自同态，它们不能直接复合。因此我们为效应复合定义一个新运算：

定义 9. 给定函数 $f , g \in { \mathfrak { E } } _ { \Gamma }$ ，定义其效应复合 $f \diamond g$ 为：

$$
\begin{array}{r c l}f \diamond g&:&\Gamma \rightarrow \partial \Gamma\\&&\mathbf {l e t} (\delta , s) = g (\gamma) \mathbf {i n}\\f \diamond g&=&\gamma \mapsto \mathbf {l e t} (\varepsilon , t) = f (\delta) \mathbf {i n}\\&&(\varepsilon , s \circ t)\end{array}\tag{13}
$$

定理 10. 效应复合把 $\mathfrak { T } _ { \Gamma }$ 的幺半群结构转移到 $\mathfrak { E } _ { \Gamma }$ 。即，

1. $( { \mathfrak { E } } _ { \Gamma } , \circ )$ 是以 $\eta _ { \Gamma } : = \gamma \mapsto ( \gamma , \mathrm { i d } _ { \Gamma } ) ;$ 为单位的幺半群；

2. 赋值 $( f , g ) \mapsto \gamma \mapsto ( f ( \gamma ) , g )$ 是从 $\mathfrak { T } _ { \Gamma }$ 到 $\mathfrak { E } _ { \Gamma }$ 的幺半群同态

证明.

1. 结合性和单位律由 $\circ _ { \bullet }$ 的那些逐分量得到。

2. 写 $e _ { i } = \gamma \mapsto ( f _ { i } ( \gamma ) , g _ { i } ) .$ ；则 $( e _ { 1 } \diamond e _ { 2 } ) ( \gamma ) = ( f _ { 1 } ( f _ { 2 } ( \gamma ) ) , g _ { 2 } \circ g _ { 1 } )$ ，它是 $\left( f _ { 1 } , g _ { 1 } \right) \circ \left( f _ { 2 } , g _ { 2 } \right)$ 的像，且 $( \mathrm { i d } _ { \Gamma } , \mathrm { i d } _ { \Gamma } )$ 映到 $\mathfrak { E } _ { \Gamma }$。 □

定理 11. 见证在效应复合下保持，且一致逆在每个状态均构成见证。即，

1. $\mathfrak { E } _ { \Gamma } ^ { * }$ 是 $\mathfrak { E } _ { \Gamma } \ :$ 的子幺半群；

2. 定理 10 的同态把每个满足 $g \circ f = \operatorname { i d } _ { \Gamma }$ 的对送入 ${ \mathfrak { E } } _ { \Gamma } ^ { * }$ 。

1. 单位元位于 $\mathfrak { E } _ { \Gamma } ^ { * }$ 中，因为 $\operatorname { i d } _ { \Gamma } ( \gamma ) = \gamma .$ 。对封闭性，取 $f , g \in { \mathfrak { E } } _ { \Gamma } ^ { * }$ 和任意 $\gamma \in \Gamma ,$ ，并令 $( \delta , s ) = g ( \gamma ) , ( \varepsilon , t ) = f ( \delta )$ ，从而 $( f \diamond g ) ( \gamma ) = ( \varepsilon , s \circ t )$ 。则 $s ( \delta ) = \gamma$ 且 $t ( \varepsilon ) = \delta ,$ 因此 $( s \circ t ) ( \varepsilon ) = s ( \delta ) = \gamma$

2. $g \circ f = \operatorname { i d } _ { \Gamma } \operatorname { g i v e s } g ( f ( \gamma ) ) = \gamma$ 在每个 γ 处成立，因此这样的对的像在每个状态都被见证。 □

正如 track 把 Γ 上的变换对提升到 $\partial \Gamma ,$ 我们定义 effect 把 $\mathfrak { E } _ { \Gamma }$ 提升到 ${ \mathfrak { E } } _ { \partial \Gamma }$：

定义 12. 定义效应函数变换 effect 为：

$$
\begin{array}{r c l r c l r c l}\mathrm{effect} _ {\Gamma}&:&\mathfrak {E} _ {\Gamma}&\rightarrow&\partial \Gamma&\rightarrow&\partial^ {2} \Gamma\\\mathrm{effect} _ {\Gamma}&=&e&\mapsto&(\gamma , \varphi)&\mapsto&\mathbf {l e t} (\delta , g) = e (\gamma) \mathbf {i n}\\&&&&&&((\delta , \varphi \circ g), \mathrm{track} _ {\Gamma} (g, \mathrm{pr} _ {1} \circ e))\end{array}\tag{14}
$$

由于 $\mathrm { e f f e c t } _ { \Gamma } ( e )$ 本身是 ${ \mathfrak { E } } _ { \partial \Gamma } ,$ ，它返回的逆是在定义 8 的意义上高一层读出的逆。该逆本身是交换效应的两个方向所得之对的 track。普通跟踪规则再次适用：撤销效应本身就是一个效应，用 ${ \mathit { g } }$ 变换状态，而撤销它的方式是再次执行该效应，这正是 $\mathrm { p r } _ { 1 } \circ e$ 所做的。因此逆被复合到交给它的累加器上，正如 track 所规定的那样。

我们现在可以为 effect 证明与 track 类似的性质。

定理 13. effect 保持 ⋄ 运算。即，$\forall f , g \in \mathfrak { E } _ { \Gamma }$

$$
\mathrm{effect} _ {\Gamma} (f) \diamond \mathrm{effect} _ {\Gamma} (g) = \mathrm{effect} _ {\Gamma} (f \diamond g)\tag{15}
$$

证明. 取任意 $( \gamma , \varphi ) \in \partial \Gamma$ ，并令 $( \delta , s ) = g ( \gamma )$ 和 $( \varepsilon , t ) = f ( \delta )$ ，从而 $( f \diamond g ) ( \gamma ) = ( \varepsilon , s \circ t )$ 且 $\operatorname { p r } _ { 1 } \circ ( f \circ g ) = ( \operatorname { p r } _ { 1 } \circ f ) \circ ( \operatorname { p r } _ { 1 } \circ g )$ 。则

$$
\begin{array}{r l} & (\mathrm{effect} _ {\Gamma} (f) \diamond \mathrm{effect} _ {\Gamma} (g)) (\gamma , \varphi) = ((\varepsilon , \varphi \circ s \circ t), \mathrm{track} _ {\Gamma} (s, \mathrm{pr} _ {1} \circ g) \circ \mathrm{track} _ {\Gamma} (t, \mathrm{pr} _ {1} \circ f)) \\ & \qquad = ((\varepsilon , \varphi \circ s \circ t), \mathrm{track} _ {\Gamma} (s \circ t, (\mathrm{pr} _ {1} \circ f) \circ (\mathrm{pr} _ {1} \circ g))) \\ & \qquad = \mathrm{effect} _ {\Gamma} (f \diamond g) (\gamma , \varphi) \end{array}
$$

其中第一步在 $( \gamma , \varphi )$ 和 $( \delta , \varphi \circ s )$ 处展开定义 12，第二步是定理 $5 ,$ 第三步折叠定义 12。 □

两个层次如何关联由下图说明。其上三角形是 $e ,$ 的见证条件（按定义 $8$ ），其下三角形是 $e ^ { \prime }$ 是否以 e 的方式被见证的问题。

![](images/a03a254bea764e6a658c2481d9a59b385917bc3626fc9dd5d3055e193b721da9.jpg)

在层次之间，投影 $\mathrm { p r } _ { 1 }$ 把每个被提升的映射与它所提升的映射关联起来，正如它对 track 在定理 4 中所做的那样。

定理 14. 令 $e \in { \mathfrak { E } } _ { \Gamma } .$ ，写 $f : = \mathrm { p r } _ { 1 } \circ e ,$ ，并令 $e ^ { \prime } : = \mathrm { e f f e c t } _ { \Gamma } ( e )$ ，其正向映射为 $f ^ { \prime } : = \mathrm { p r } _ { 1 } \circ$ $e ^ { \prime } .$ 。则

1. $\mathrm { p r } _ { 1 } \circ f ^ { \prime } = f \circ \mathrm { p r } _ { 1 } ;$

2. 对每个 $( \gamma , \varphi ) \in \partial \Gamma$ ，在此见证的提升逆 $g ^ { \prime } : = \mathrm { p r } _ { 2 } ( e ^ { \prime } ( \gamma , \varphi ) )$ 与逆 $g : = \mathrm { p r } _ { 2 } ( e ( \gamma ) )$ 满足 $\operatorname { p r } _ { 1 } \circ g ^ { \prime } = g \circ \operatorname { p r } _ { 1 }$

证明.

1. 由定义 12，$f ^ { \prime } ( \gamma , \varphi ) = ( f ( \gamma ) , \varphi \circ g )$ ，其状态为 $f ( \gamma ) = ( f \circ \operatorname { p r } _ { 1 } ) ( \gamma , \varphi )$

2. 这是把定理 4 应用于 $g ^ { \prime } = \operatorname { t r a c k } _ { \Gamma } ( g , f )$

下三角形是否闭合由计算提升逆返回的内容来确定：

定理 15. 令 $e \in \mathfrak { E } _ { \Gamma } ^ { * }$ 并写 $f : = \mathrm { p r } _ { 1 } \circ e$ 。固定 $( \gamma , \varphi ) \in \partial \Gamma$ ，令 $( \delta , g ) = e ( \gamma )$ ，并把 $( \Delta , g ^ { \prime } )$ 写作 effe $\operatorname { c t } _ { \Gamma } ( e ) \mathrm { a t } \left( \gamma , \varphi \right)$ 的值。则

$$
g ^ {\prime} (\Delta) = (\gamma , \varphi \circ g \circ f)\tag{16}
$$

状态被精确恢复。累加器也被恢复，等价地 $\mathrm { e f f e c t } _ { \Gamma } ( e ) \in { \mathfrak { E } } _ { \partial \Gamma } ^ { * }$ ，当且仅当 $g \circ f = \operatorname { i d } _ { \Gamma } ;$ ；且在每种情形下 $( \varphi \circ g \circ f ) ( \gamma ) = \varphi ( \gamma )$ ，因此可靠性不变量被保持。

证明. 由定义 12，$\Delta = ( \delta , \varphi \circ g )$ 且 $g ^ { \prime } = \operatorname { t r a c k } _ { \Gamma } ( g , f )$ ，因此

$$
g ^ {\prime} (\Delta) = (g (\delta), \varphi \circ g \circ f) = (\gamma , \varphi \circ g \circ f)
$$

其中用到 $g ( \delta ) = \gamma$ 。属于 ${ \mathfrak { E } } _ { \partial \Gamma } ^ { * }$ 要求这在每个输入处等于 $( \gamma , \varphi )$ ；取 $\varphi = \mathrm { i d } _ { \Gamma }$ 把累加器的相等性化为 $g \circ f = \operatorname { i d } _ { \Gamma } ,$ ，反之该条件对每个 $\varphi .$ 都给出累加器的相等性。最后 $( \varphi \circ g \circ f ) ( \gamma ) = \varphi ( g ( \delta ) ) = \varphi ( \gamma )$ □

因此下三角形仅在 $\gamma$ 处见证的逆在每个状态都逆转 $f$ 时才闭合，所以 effect 并不把 ${ \mathfrak { E } } _ { \Gamma } ^ { * }$ 送入 ${ \mathfrak { E } } _ { \partial \Gamma } ^ { * }$ 。每种情形下成立的是在 $\gamma \colon$ 处的吻合，即 recover $\mathrm { \ i } _ { \Gamma } ( g ^ { \prime } ( \Delta ) ) = \mathrm { r e c o v e r } _ { \Gamma } ( \gamma , \varphi )$ ，这恰是定理 $7$ 对累加器所假设的全部，因此逆转不会触动恢复目标。

以与应用相反的顺序逆转效应无需任何额外条件，因为每个逆此时都面对它自身应用所产生的状态：

定理 16. 令 $e _ { 1 } , \cdots , e _ { n } \in \mathfrak { E } _ { \Gamma } ^ { * }$ 从 $( \gamma _ { 0 } , \mathrm { i d } _ { \Gamma } )$ 按顺序应用并以相反顺序逆转。则

1. 每次逆转都恢复其应用所针对的上下文状态；

2. 每个中间状态满足可靠性不变量。

证明. 每一步是一次应用或一次逆转。一次应用把 $( \gamma , \varphi )$ 带到 $( \delta , \varphi \circ g )$ 且 $g ( \delta ) = \gamma$ ，因此由定理 $^ { 7 , }$ 它保持 $\varphi ( \gamma )$ ，其假设恰是 ${ \mathfrak { E } } _ { \Gamma } ^ { * }$ 的见证。按相反顺序逆转使每个逆面对它自身应用所产生的状态，因此由定理 15 该逆转精确恢复前一个状态并同样保持 $\varphi ( \gamma )$ ；这两个结论都不依赖逆所接收的累加器。 □

## 3.1.3. 效应的独立性（Independence of Effects）

在效应自身应用所产生的状态处逆转效应是定理 16 所覆盖的；在任意其他状态处逆转效应是本小节所覆盖的。后一种情况有两种情形。逆可能在后来的效应仍然在位时运行，这相当于把一个组件从运行中的系统撤出；一个序列可能交错多个组件的效应，每个组件保留自己的逆，从而一个组件的逆被另一个组件的应用所分隔。在这两种情形下，逆面对的是外来效应已移动的状态，而它是否仍然逆转它被构造来逆转的东西是一个交换性问题：必须交换的是每个效应能执行的每个变换与另一个效应能执行的每个变换，正向映射与产生的逆都一样。单个累加器都无法解决这两种情形，$\varphi$ 是以一种顺序、一次性运行它持有的每个逆的复合。

定义 17. 对效应函数 $e \in { \mathfrak { E } } _ { \Gamma }$ ，变换幺半群 ${ \mathfrak { M } } ( e )$ 是由 f 的正向映射连同 e 产生的每个逆所生成的 $\Gamma  \Gamma$ 的子幺半群，而 ${ \mathfrak { M } } ( e )$ 的生成元是该生成集的元素：

$$
\mathfrak {M} (e) := \left\langle \left\{\operatorname{pr} _ {1} \circ e \right\} \cup \left\{\operatorname{pr} _ {2} (e (\gamma)) \mid \gamma \in \Gamma \right\} \right\rangle\tag{17}
$$

由对 $( f , g ) \in \mathfrak { T } _ { \Gamma }$ 诱导的效应以 f 和 g 为其生成元，它产生的逆在每个状态都是 g。

引理 18. 交换性在生成元上解决，且 ⋄ 不扩大任何变换幺半群。即，

1. 若 $\mathfrak { M } ( e _ { 1 } )$ 的每个生成元与 $\mathfrak { M } ( e _ { 2 } )$ 的每个生成元交换，则 $\mathfrak { M } ( e _ { 1 } )$ 的每个元素与 ${ \mathfrak { M } } ( e _ { 2 } )$ 的每个元素交换；

2. $\mathfrak { M } ( e _ { 1 } \circ e _ { 2 } ) \subseteq \langle \mathfrak { M } ( e _ { 1 } ) \cup \mathfrak { M } ( e _ { 2 } ) \rangle$

证明.

1. 与 $\mathfrak { M } ( e _ { 2 } )$ 的每个生成元交换的映射构成 $\Gamma  \Gamma ,$ 的子幺半群，因为 $\mathrm { i d } _ { \Gamma }$ 位于其中，且 f 和 $f ^ { \prime }$ 交换处 $f \circ f ^ { \prime }$ 也交换。该子幺半群按假设包含 $\mathfrak { M } ( e _ { 1 } )$ 的生成元，因此包含 $\mathfrak { M } ( e _ { 1 } )$ 。固定 $f \in \Re ( e _ { 1 } )$ ，与 f 交换的映射同样构成包含 $\mathfrak { M } ( e _ { 2 } )$ 的生成元、因而包含 $\mathfrak { M } ( e _ { 2 } )$ 的子幺半群

2. 由定义 9，$e _ { 1 } \diamond e _ { 2 } \mathrm { i } \mathbf { s } \left( \mathrm { p r } _ { 1 } \circ e _ { 1 } \right) \circ \left( \mathrm { p r } _ { 1 } \circ e _ { 2 } \right)$ 的正向映射是复合，而它在任意状态产生的逆是 $s \circ t$ ，其中 s 由 $e _ { 2 }$ 产生、t 由 $e _ { 1 }$ 产生。因此 ${ \mathfrak { M } } ( e _ { 1 } \circ$ $e _ { 2 } )$ 的每个生成元都是两者生成元的复合。 □

定义 19. 效应函数 $e _ { 1 } , e _ { 2 } \in \mathfrak { E } _ { \Gamma }$ 是独立的，当

1. 一个的每个变换与另一个的每个变换交换，

$$
\forall f \in \mathfrak {M} (e _ {1}), g \in \mathfrak {M} (e _ {2}). \quad f \circ g = g \circ f\tag{18}
$$

2. 一方的变换不扰动另一方产生的逆，

$$
\forall g \in \mathfrak {M} (e _ {2}), \gamma \in \Gamma . \quad \mathrm{pr} _ {2} (e _ {1} (g (\gamma))) = \mathrm{pr} _ {2} (e _ {1} (\gamma))\tag{19}
$$

且交换 $e _ { 1 }$ 和 $e _ { 2 }$ 后同样成立。

族 $\left( \boldsymbol { e } _ { l } \right) _ { l \in L }$ 是两两独立的，当对每个 ${ \mathit { l } } \neq { \mathit { l } } ^ { \prime }$ ，$e _ { l }$ 和 $e _ { l ^ { \prime } }$ 独立。族可以重复同一个效应函数，而把某效应保持为与自身独立即保持 M(e) 交换。

对由对 $( f _ { 1 } , g _ { 1 } )$ 和 $\left( f _ { 2 } , g _ { 2 } \right)$ 诱导的效应，条款 (1) 由引理 18(1) 即四对的交换性 $f _ { 1 } , f _ { 2 } ; g _ { 1 } , g _ { 2 } ; f _ { 1 } , g _ { 2 } ;$ 与 $g _ { 1 } , f _ { 2 } ,$ ，而条款 (2) 无条件成立，诱导效应在每个状态产生一个逆。⋄ 下的交换是不同性质。$e _ { 1 } \diamond e _ { 2 } = e _ { 2 } \diamond e _ { 1 }$ 所等同的是两个顺序的复合正向映射彼此、两个顺序的复合逆彼此，每个逆在其自身应用所产生的状态处进入复合；独立性相反地把一个效应的每个变换与另一个效应的每个变换关联起来，包括正向映射与外来逆配对。

在独立性下，逆可以在后来效应已移动的状态处运行，而它在那里撤出的只是它自己的贡献，别无其他：

定理 20. 令 $e _ { 1 } , \cdots , e _ { n } \in \mathfrak { E } _ { \Gamma } ^ { * }$ 两两独立并从 $\gamma _ { 0 }$ 按顺序应用。写 $f _ { i } : = \mathbf { p r } _ { 1 } \circ e _ { i } ,$ ，令 $\delta _ { i } : = f _ { i } ( \delta _ { i - 1 } )$ 且 $\delta _ { 0 } : = \gamma _ { 0 } .$ ，并令 $g _ { i } : = \mathrm { p r } _ { 2 } ( e _ { i } ( \delta _ { i - 1 } ) )$ 为 $e _ { i }$ 在被应用处产生的逆。固定 j 并写 $\delta _ { i } ^ { \prime } : = \big ( f _ { i } \circ \cdots \circ f _ { j + 1 } \big ) \big ( \delta _ { j - 1 } \big )$ 为省略 $e _ { j }$ 后序列的状态，从而 $\delta _ { j } ^ { \prime } = \delta _ { j - 1 }$ 。则对每个满足 $j \leq u \leq n$ 的 u

1. $\delta _ { u } = f _ { j } ( \delta _ { u } ^ { \prime } )$ 且 $g _ { j } ( \delta _ { u } ) = \delta _ { u } ^ { \prime } ,$

2. 每个满足 $i > j$ 的 $e _ { i }$ 在 $\delta _ { i - 1 } ^ { \prime }$ 处产生的逆 $g _ { i }$ 与它在 $\delta _ { i - 1 }$ 处产生的一致。

证明.

1. 第一个等式是对 u 的归纳。在 $u = j$ 处它读作 $\delta _ { j } = f _ { j } \big ( \delta _ { j - 1 } \big )$ ，即 $\delta _ { j }$ 的定义。对归纳步，$\delta _ { u + 1 } = f _ { u + 1 } ( \delta _ { u } ) = f _ { u + 1 } ( f _ { j } ( \delta _ { u } ^ { \prime } ) ) = f _ { j } ( f _ { u + 1 } ( \delta _ { u } ^ { \prime } ) ) =$ $f _ { j } \left( \delta _ { u + 1 } ^ { \prime } \right)$ ，中间等式是定义 19 的条款 (1) 应用于 $e _ { u + 1 }$ 和 $e _ { j } ,$ 它们是族中不同效应，因为 $u + 1 > j$ 。对第二个等式，条款 (1) 把 $g _ { j }$ 穿过 $e _ { j }$ 之后应用的正向映射带出，把 $e _ { j }$ 的见证留到它成立的那个状态使用：

$$
g _ {j} \left(\delta_ {u}\right) = \left(g _ {j} \circ f _ {u} \circ \dots \circ f _ {j + 1}\right) \left(\delta_ {j}\right) = \left(f _ {u} \circ \dots \circ f _ {j + 1}\right) \left(g _ {j} \left(f _ {j} \left(\delta_ {j - 1}\right)\right)\right) = \delta_ {u} ^ {\prime}
$$

最后一个等式依赖 $g _ { j } \big ( f _ { j } \big ( \delta _ { j - 1 } \big ) \big ) = \delta _ { j - 1 } ,$ ，即定义 8 在 $\delta _ { j - 1 }$ 处对 $e _ { j }$ 要求的见证

2. 由 (1)，状态 $\delta _ { i - 1 }$ 是 $f _ { j } ( \delta _ { i - 1 } ^ { \prime } )$ ，且 $f _ { j } \in \mathfrak { M } ( e _ { j } )$ ，因此定义 19 对 $e _ { i }$ 和 $e _ { j } \mathrm { g i v e s p r } _ { 2 } \big ( e _ { i } \big ( f _ { j } ( \delta _ { i - 1 } ^ { \prime } ) \big ) \big ) = \mathrm { p r } _ { 2 } \big ( e _ { i } ( \delta _ { i - 1 } ^ { \prime } ) \big )$ □

条款 (1) 定位逆所达到的状态：它就是同一序列在效应从未被应用的情况下会达到的状态，无论之后应用了什么效应。条款 (2) 定位其他逆在那里持有的东西，两者合在一起使该定理可以再次应用于更短的序列：

推论 21. 令 $e _ { 1 } , \cdots , e _ { n } \in \mathfrak { E } _ { \Gamma } ^ { * }$ 两两独立并从 $\gamma _ { 0 } ,$ 按顺序应用，并令 $g _ { 1 } , \cdots , g _ { n }$ 如上。按 $\{ 1 , \cdots , n \}$ 的任意置换的顺序在 $\delta _ { n }$ 处应用这些逆可达到 $\gamma _ { 0 }$

证明. 对 j 向下归纳。令置换以 j 开始。由定理 $2 0 ( 1 )$ 在 $\delta _ { n }$ 处应用 $g _ { j }$ 达到 $\delta _ { n } ^ { \prime } .$ ，即省略 $e _ { j }$ 的序列所达到的状态，并由定理 20(2)，剩余效应在此产生的逆就是手中的 $g _ { i }$ 。该序列两两独立，因为它是子族，所以归纳假设适用于它和置换的其余部分；空序列达到 $\gamma _ { 0 }$ □

LIFO 顺序就是这样一个置换，而定理 16 在无任何假设的情况下按此顺序逆转。独立性带来的是所有其他顺序，以及随之而来的、交错多个组件的序列，第 4.4.2 节将其推广到整个系统的迹。

这些构造合在一起构成可逆效应：${ \mathfrak { E } } _ { \Gamma } ^ { * }$ 中的每个效应函数显式提供自己的逆，effect 在效应上下文 $\partial \Gamma ,$ 上跟踪这些逆，⋄ 运算在保持可逆性的同时组合它们。它们交付的是局部时间可组合性，说它局部是因为该保证是针对一个组件的效应本身来读的。我们把这个保证表述为如下准则：对组件应用的一列效应函数中的每个序列，累加器恢复它开始的上下文（定理 7），且逆转该序列使每个逆面对它自身应用所针对的状态（定理 16）。加载组件即应用这样的序列并把其逆累积在 $\varphi ;$ 中；卸载组件即应用它。

准则遗漏了两件事，而两者都在多个组件在场时出现：按累加器所强加顺序之外的顺序逆转，以及交错其他效应的一个序列。独立性交付它们（推论 21），且它是关于效应的条件而非构造的性质，第 3.3.2 节识别满足它的纪律，第 4.4.2 节对整个系统迹读出该保证。独立性失败之处，顺序必须由他处承载：在一个组件内由累加器承载，它无论效应如何都按 LIFO 顺序逆转（第 4.3.2 节），在组件间由声明的余效应承载，它把一个激活排到另一个激活之前（第 4.3.1 节）。

## 3.2. 响应式余效应（Reactive Coeffects）

空间可组合性是指组件能够声明彼此之间的依赖，系统能够在运行时解析、提供和撤出这些依赖的能力。这要求每当共享上下文改变时重新评估依赖满足情况，从而使组件在其依赖可用时激活、在其依赖被撤出时停用。因此我们把组件的依赖建模为一个规范，并把上下文的每次变化依据该规范分类为激活、停用或中性。依据规范分类正是检测满足情况变化的方式；响应这种分类驱动激活与停用。我们称这样的余效应是响应式的：通过分类上下文变化并据此驱动激活和停用，正确的余效应排序成为结构性保证。

## 3.2.1. 余效应上下文（Coeffect Context）

传统的控制反转（inversion-of-control, IoC）容器 [38] 通常把依赖建模为简单的键值映射。本节把 IoC 形式化为与可逆效应协同的余效应上下文，为动态组合提供数学基础。

定义 22. 给定类型族 $\nu : K \to$ Type，定义余效应上下文为依赖的部分函数类型：

$$
\Sigma := (k: K) \rightharpoonup \mathcal {V} _ {k}\tag{20}
$$

其中 $\sigma : \Sigma$ 是有限部分函数，为每个 $k \in \mathrm { d o m } ( \sigma ) \subseteq K$ 赋予 $\nu _ { k }$ 类型的值。我们写：

$\sigma ( k )$ 表示应用（当 $k \in \mathrm { d o m } ( \sigma ) )$ 时有定义）

$\sigma [ k \mapsto v ]$ 表示在 v 处绑定 k、在别处与 σ 一致的表格；

$\sigma \setminus$ k 表示限制（当 $k \in \mathrm { d o m } ( \sigma ) ) .$ 时有定义）

$k \in \mathrm { d o m } ( \sigma )$ 表示成员资格。

类型族 K 的使用确保每个依赖键 k 与特定的值类型 $\nu _ { k } ,$ 相关联，为依赖访问提供静态类型安全。扩展和限制带有由下面的操作施加的前置条件：依赖不能被提供两次（扩展要求 k ∉ dom(σ)），也不能在缺席时被撤销（限制要求 $( k \in \mathrm { d o m } ( \sigma )$ ）。违反前置条件被报告为错误且不产生转移，因此描述实际发生转移的效应代数对这些操作原封不动地适用。偏好将失败内化的读者可以把下面的每个 $\Sigma  \Sigma$ 读作 $\Sigma  \mathsf { M a y b e } ( \Sigma )$ 并在 Maybe 单子（第 2.1 节）中复合，代价是用操作定义域上的部分恒等替换每个恒等。基于此上下文结构，我们定义两个核心操作：

定义 23. 在 Σ 上定义 get 和 set 操作：

$$
\begin{array}{r c l r c l}\text {get}&:&(k: K)&\to&\Sigma&\rightharpoonup\\\text {get}&=&k&\mapsto&\sigma&\mapsto\\\text {set}&:&(k: K) \times \mathcal {V} _ {k}&\to&\Sigma&\rightharpoonup\\\text {set}&=&(k, v)&\mapsto&\sigma&\mapsto\end{array}\qquad\begin{array}{r c l r c l}\mathcal {V} _ {k}\\\sigma (k)\\\Sigma \times (\Sigma \rightharpoonup \Sigma)\\(\sigma [ k \mapsto v ], \lambda \sigma^ {\prime}. \sigma^ {\prime} \setminus k)\end{array}\tag{21}
$$

其中 get(k) 要求 $k \in \mathrm { d o m } ( \sigma )$ 且 $\operatorname { s e t } ( k , v )$ 要求 k ∉ dom(σ) 作为前置条件。

值得注意的是，set $( k , v )$ 具有类型 $\mathfrak { E } _ { \Sigma } ^ { * } ,$ 恰是余效应上下文上的效应函数。因此我们可以直接应用第 3.1 节的效应机制：effect 提供依赖注册的自动跟踪与恢复。这就是响应式余效应与可逆效应之间的协同：余效应操作是效应，而效应是可逆的。

get 交给组件的是一个值，而组件能对这个值做什么取决于该键处的余效应提供什么。因此一个键承载的不仅仅是值类型：

定义 24. 键 k 处的余效应是三元组 $\left( \mathcal { V } _ { k } , _ { \widetilde { k } } , \mathcal { A } _ { k } \right)$ ，其中 $\nu _ { k }$ 是定义 22 的值类型，$\widetilde { \overline { { k } } }$ 是 $\nu _ { k }$ 上的等价关系，k 处的值在其下进行比较（第 3.3.2 节），而 $\mathcal { A } _ { k }$ 是余效应操作集，即绑定在 k 处的值向持有它的组件提供的操作。操作 $a \in \mathcal A _ { k }$ 携带参数类型 $X _ { a }$ 和结果类型 $B _ { a } ,$ 并且只作用于该值：

$$
a: X _ {a} \to \mathcal {V} _ {k} \rightharpoonup \mathcal {V} _ {k} \times (\mathcal {V} _ {k} \rightharpoonup \mathcal {V} _ {k}) \times B _ {a}\tag{22}
$$

其前两个构成部分形成 $\nu _ { k }$ 上的效应函数，按定义 8 的要求被见证，第三个是结果。每个操作都被要求尊重 ≃：在 ≃-相关值处，它在两者处都有定义或都没有定义，并且有定义处它产生 ${ \widetilde { \overline { { k } } } } ^ { . }$ -相关的后继、再次把 ${ \widetilde { \overline { { k } } } }$ -相关值带到 ≃-相关值的逆，以及相等的结果。操作通过其 $l i f t$ 作用于余效应上下文

$$
a ^ {\Sigma} (x) (\sigma) := \operatorname{let} (v, g, b) = a (x) (\sigma (k)) \text {   in   } (\sigma [ k \mapsto v ], \lambda \sigma^ {\prime}. \sigma^ {\prime} [ k \mapsto g (\sigma^ {\prime} (k)) ], b)\tag{23}
$$

当 $k \in \mathrm { d o m } ( \sigma )$ 时有定义，其前两个构成部分是 Σ 上的效应函数。

把 k 的操作类型化在 $\nu _ { k }$ 上正是把它限制在 k 处的绑定上：lift 读写该绑定并保持每个其他键原样，因此无需旁条件即可如此说明。隔离生效处，它到达的绑定是领域解析到的那个（定义 28），共享一个领域的两个键共享一个绑定。行为转而依赖另一键的操作把该键的值读入其参数 $X _ { a } ,$ 而下一小节的响应式纪律在读取它的组件运行的整个期间保持该值固定（定理 63）。

## 3.2.2. 规范与通知（Specification and Notification）

前面的定义描述了单个依赖如何被注册和访问。然而，访问缺席的依赖是运行时失败。因此组件应当只在它声明的所有依赖都出现时才激活，而不是乐观地访问并在缺失时失败。这引出两个问题：组件声明的依赖是否被共同满足，以及当该状态改变时系统应如何响应。余效应上下文 Σ 携带一种自然的观测结构，使两个问题都可处理：对任意余效应规范 $d \subseteq K .$ ，定义满足谓词：

$$
\sigma \vDash d := \forall k \in d. k \in \operatorname{dom} (\sigma)\tag{24}
$$

该谓词是可判定的（因为 dom(σ) 是有限的）。由于对 $\sigma$ 的所有变更都经过效应函数（其逆恢复先前的定义域），满足情况的变化在每个效应边界都是可检测的。这就是响应性的代数基础：效应系统保证每次余效应变化都被观测到。

定义 25. 余效应规范是：

$$
\mathfrak {D} _ {\Sigma} := \operatorname{Set} (K)\tag{25}
$$

表示组件向环境声明的依赖集。

使这个规范具有响应性的是它如何分类状态转移。任何把 $\sigma$ 变换为 $\sigma ^ { \prime }$ 的效应都可以由规范 $d \in \mathfrak { D } _ { \Sigma }$ 依据 d 的满足状态是否被改变来分类：

定义 26. 给定余效应规范 $d \subseteq K$ 和状态 $\sigma , \sigma ^ { \prime } \in \Sigma$ ，定义：

$$
\text { notify } _ {d} (\sigma , \sigma^ {\prime}) := \left\{ \begin{array}{l l} \text { activating } & \text { if   } \sigma \not \models d \land \sigma^ {\prime} \models d \\ \text { deactivating } & \text { if   } \sigma \models d \land \sigma^ {\prime} \not \models d \\ \text { neutral } & \text { otherwise } \end{array} \right.\tag{26}
$$

这是良定义的，因为 $\sigma \models d$ 可判定且所有状态转移都由效应函数中介。响应式不变量是：激活转移触发组件效应的执行（带完全效应跟踪），而停用转移通过应用累加器触发恢复。这些转移的精确操作语义取决于它们与控制流的交互，将在第 4 节中展开。

set 和 notify 一起交付局部空间可组合性，说它局部与前述同样的意义，该保证是针对一个组件的余效应本身来读的。我们把这个保证表述为如下准则：组件只在满足其规范的状态处激活，因此它从不读取缺席的绑定，且上下文的每次变化都依据该规范被分类，因此满足性的丧失在其发生处被检测并驱动停用。两半都直接由上述定义得出，满足性是组件将要激活处检查的前置条件，而 $\mathrm { n o t i f y } _ { d }$ 在每个转移处都有定义。

准则覆盖了余效应排序的一个方向而非另一个。若组件 A 提供键 k 且组件 B 声明 $k \in d _ { B } ,$ 则 B 只能在 A 激活并提供 $k ,$ 之后激活，因为 ${ \boldsymbol { \sigma } } \models d _ { B }$ 要求 $k \in \mathrm { d o m } ( \sigma )$ 。反之则不成立：卸载 A 把 A 从 dom(σ) 中移除从而破坏 B 的满足性，但通知本身既不能使 B 在 $B ^ { \prime } { \mathrm { s } }$ 自身拆卸所需的整个期间保持可读，也不能推迟 B 的恢复直至 A 完成。把撤出排到它所造成的停用之后是对其他组件而非行动组件的条件，因此属于该保证的全局形式，第 4.3.1 节提供所需的机制。

## 3.2.3. 隔离与拦截（Isolation and Interception）

基本余效应上下文 Σ 建模扁平的依赖表。然而在实践中，系统可能需要为不同的组件把不同的值绑定到同一个逻辑依赖。本节用两种机制扩展余效应上下文：余效应隔离（同一键在不同上下文中解析不同）和余效应拦截（依赖访问上的横切行为）。

实现。这两种机制与 get 和 set 不同之处在于它们作用的对象。提供（provision）写入每个组件都读取的共享表，因此它是该表上的效应并携带撤出它的逆。相反，隔离与拦截调整一个键在一个上下文下的组件如何被解析，使表本身保持原样。把操作类型化为效应固定其外延（denotation）——后继状态与逆的配对——但不固定其实现，实现决定逆如何被执行。

定义 27. 上下文上的效应函数容许两种实现：

• 原位实现（In-place realization）改变上下文并返回一个非平凡逆；后继与输入共享别名，恢复运行逆以撤销该变更。

• 派生实现（Derived realization）保持输入原样并返回从它派生的全新上下文，以其恒等为逆；恢复丢弃派生上下文。从另一上下文派生的上下文正是定义 32 的递归结构所承载的。

在纯函数设定下两者重合，而命令式宿主可以为每个操作任选其一；第 5.1.2 节实现两者。隔离和拦截被直接赋予派生实现：每个都产生一个全新上下文，其自有表与继承的表不同，因此每个都在下面被类型化为上下文到上下文的映射而非效应函数。共享表中无任何变化，因此没有要跟踪的逆，也没有定义 12 要提升的东西，恢复把派生上下文连同它承载的调整一起丢弃。在派生表上赋值会覆盖继承表在键处持有的值，这就是两个操作都不携带前置条件的原因。

余效应隔离。通过引入隔离领域，余效应隔离允许同一依赖在不同上下文中绑定不同的值。这在多租户系统、测试环境和组件沙箱中有广泛的应用。

定义 28. 定义带隔离的余效应上下文为：

$$
\Sigma^ {\mathrm{iso}} := (K \rightharpoonup R) \times ((r: R) \rightharpoonup \mathcal {V} _ {r})\tag{27}
$$

它可以表示为二元组 $( \rho , \sigma )$ ，其中：

$\rho : K  R$ 是隔离领域表，为每个被隔离的键赋予领域标识符；dom $( \rho )$ 之外的键解析到自己的领域，因此那里我们写 $\rho ( k ) = k$ $( R \supseteq K )$ ；

$\sigma : ( r : R )  \mathcal { V } _ { r }$ 是依赖表，从领域标识符到类型化值的部分依赖函数。

两层映射结构把逻辑层与存储层解耦，使依赖访问具有上下文感知性。访问键 $k ,$ 时，系统首先解析 $\rho ( k )$ 获得领域标识符 $^ { r , }$ 然后访问 $\sigma ( r )$ 获取实际值。

定义 29. $\Sigma ^ { \mathrm { i s o } }$ 上的 get、set 和 isolate 操作是：

$$
\begin{array}{r c l r c l r c l}\text {get}&:&(k: K)&\to&\Sigma^ {\mathrm{iso}}&\rightharpoonup&\mathcal {V} _ {\rho (k)}\\\text {get}&=&k&\mapsto&(\rho , \sigma)&\mapsto&\sigma (\rho (k))\\\text {set}&:&(k: K) \times \mathcal {V} _ {\rho (k)}&\to&\Sigma^ {\mathrm{iso}}&\rightharpoonup&\Sigma^ {\mathrm{iso}} \times (\Sigma^ {\mathrm{iso}} \rightharpoonup \Sigma^ {\mathrm{iso}})\\\text {set}&=&(k, v)&\mapsto&(\rho , \sigma)&\mapsto&((\rho , \sigma [ \rho (k) \mapsto v ]),   \lambda (\rho^ {\prime}, \sigma^ {\prime}). (\rho^ {\prime}, \sigma^ {\prime} \setminus \rho^ {\prime} (k)))\\\text {isolate}&:&K \times R&\to&\Sigma^ {\mathrm{iso}}&\to&\Sigma^ {\mathrm{iso}}\\\text {isolate}&=&(k, r)&\mapsto&(\rho , \sigma)&\mapsto&(\rho [ k \mapsto r ], \sigma)\end{array}\tag{28}
$$

其中 get 和 set 携带沿 $\rho ,$ 搬运的定义 23 的前置条件，即 $\rho ( k ) \in$ dom(σ) 和 $\rho ( k ) \notin \mathrm { d o m } ( \sigma )$ 。isolate $( k , r )$ 派生的上下文把领域 r 赋予 k 并原样继承依赖表，因此已隔离的键被重新指派而非拒绝。

余效应隔离机制本质上实现了一个运行时临时多态系统。通过隔离领域标识符，同一依赖键可以在不同上下文中解析到完全不同的值，且这种多态可以在运行时动态调整。与传统的依赖注入相比，余效应隔离提供更细粒度的控制，能为特定组件实现定制隔离；set 仍是效应函数 $\left( \mathfrak { E } _ { \Sigma ^ { \mathrm { { i s o } } } } ^ { * } \right)$ 从而继承可逆性，而 isolate 不需要，因为它派生上下文而非写入共享表。

余效应拦截。第二种机制，余效应拦截，把横切元数据附加到依赖访问上，在不修改依赖值的情况下添加行为。该元数据既可由上下文携带也可由组件声明，因此我们同时扩展余效应上下文与余效应规范：

定义 30. 定义带拦截的余效应上下文与规范为：

$$
\begin{array}{l}\Sigma^ {\mathrm{inter}} := ((k: K) \to \mathcal {M} _ {k}) \times ((k: K) \rightharpoonup (\mathcal {M} _ {k} \to \mathcal {V} _ {k}))\\\mathfrak {D} ^ {\mathrm{inter}} := (k: K) \rightharpoonup \mathcal {M} _ {k}\end{array}\tag{29}
$$

上下文 $\Sigma ^ { \mathrm { i n t e r } }$ 是二元组 $( \iota , \sigma ) \colon$ ι 是安装在上下文本身上的上下文携带元数据，默认为空 $\left( \epsilon _ { k } \right)$ ；ι 把每个键 k 映射到从元数据 $\mathcal { M } _ { k }$ 到值 $\nu _ { k }$ 的提供函数。规范 $d \in \mathfrak { D } ^ { \mathrm { i n t e r } }$ 携带组件声明的元数据，为每个键赋予其元数据 $d ( k )$ ，以 dom $( d )$ 作为依赖集。每个键为其元数据配备幺半群 $( \mathcal { M } _ { k } , \oplus _ { k } , \epsilon _ { k } ) \colon$ 合并 $\oplus _ { k }$ 是结合的，以 $\epsilon _ { k }$ （空元数据）为单位。

定义 31. $\Sigma ^ { \mathrm { i n t e r } }$ 上的 get、set 和 intercept 操作是：

$$
\begin{array}{r c l r c l}\text {get}&:&(k: K) \times \mathcal {M} _ {k}&\to&\Sigma^ {\mathrm{inter}}&\rightharpoonup\\\text {get}&=&(k, \mu)&\mapsto&(\iota , \sigma)&\mapsto\\\text {set}&:&(k: K) \times (\mathcal {M} _ {k} \to \mathcal {V} _ {k})&\to&\Sigma^ {\mathrm{inter}}&\rightharpoonup\\\text {set}&=&(k, \psi)&\mapsto&(\iota , \sigma)&\mapsto\\\text {intercept}&:&(k: K) \times \mathcal {M} _ {k}&\to&\Sigma^ {\mathrm{inter}}&\to\\\text {intercept}&=&(k, \nu)&\mapsto&(\iota , \sigma)&\mapsto\\\end{array}\qquad\begin{array}{r c l r c l}\mathcal {V} _ {k}\\\sigma (k) (\mu \oplus_ {k} \iota (k))\\\Sigma^ {\mathrm{inter}} \times (\Sigma^ {\mathrm{inter}} \rightharpoonup \Sigma^ {\mathrm{inter}})\\((\iota , \sigma [ k \mapsto \psi ]), \lambda (\iota^ {\prime}, \sigma^ {\prime}). (\iota^ {\prime}, \sigma^ {\prime} \setminus k))\\\Sigma^ {\mathrm{inter}}\\(\iota [ k \mapsto \iota (k) \oplus_ {k} \nu ], \sigma)\end{array}\tag{30}
$$

其中 get 和 set 携带提供函数表上定义 23 的前置条件，即 $k \in$ dom(σ) 和 $k \not \in \mathrm { d o m } ( \sigma )$ 。intercept $( k , \nu )$ 派生的上下文把 ν 合并到继承的 k 处元数据上并原样继承提供函数表。

当规范为 d 的组件访问键 k 时，系统求值 $\sigma ( k ) ( d ( k ) \oplus _ { k }$ $\iota ( k ) )$ ：组件声明的元数据与上下文携带的元数据 $\iota ,$ 合并，提供函数应用于结果。该合并遵循每个键自身的语义（例如标量字段被覆盖、集合值字段取并集）并且是右偏的，因此 ι(k) 优先并可覆盖组件的声明，让外层上下文能在不修改组件的情况下约束组件如何使用余效应（例如第 6.3 节）。

## 3.3. 上下文范式（The Context Paradigm）

第 3.1 节与第 3.2 节各自作用于一个上下文，前者作为效应的载体、后者作为余效应的载体，留下一个问题：同时承载两者的单一上下文看起来如何。本节给出这一统一的具体构造，从余效应组装出为第 3.1.3 节留下的效应独立性提供来源的观测等价，并论证所得的上下文类型自身构成一种编程范式。

## 3.3.1. 统一上下文（Unified Context）

对上下文 Γ，效应上下文 ∂Γ（第 3.1 节）提供一个更高层的抽象，承载上一层的上下文和该层的累加器（定义 2）。把此结构递归化并与其与余效应上下文 Σ 结合得到如下类型：

定义 32. 上下文类型 $\Gamma _ { \infty }$ 定义为：

$$
\Gamma_ {\infty} := \mu \Gamma . \Gamma \times (\Gamma \to \Gamma) \times \Sigma\tag{31}
$$

其中三个投影是：

• Γ：当前上下文状态（递归）；

• Γ → Γ：累加器，恢复本层的效应；

• Σ：携带依赖信息的余效应上下文。

在此定义下，effect 把 ${ \mathfrak { E } } _ { \Gamma _ { \infty } }$ 映到自身，把 Γ-塔统一为单一自相似类型。余效应上下文 Σ 在结构上被整合：依赖操作（set、get）作用于 $\Sigma ,$ 累加器跟踪其逆转。由于支撑 Σ 的类型族 K 不受约束，系统需要在组件间共享的任何状态都可以编码为具有适当值类型的依赖——Σ 涵盖所有共享可变状态，而不仅仅是组件间依赖。组件与其环境的每次交互都穿过这个单一实体。

层次组合。$\Gamma _ { \infty }$ 的递归结构支持层次控制：父上下文聚合多个子层效应，形成树形控制结构，在保持模块性的同时支持统一的跨层管理。effect 变换实现了字面的「即插即用」隐喻：

• 加载组件对应于执行其效应（插入）；

• 卸载组件对应于恢复其效应（拔出，不影响其他运行中的组件）；

• 层次中不同层的组件可独立加载和卸载；父上下文聚合并管理其所有子节点的效应，支持任意嵌套的组合。

## 3.3.2. 观测等价（Observational Equivalence）

第 3.1 节的恢复保证断言状态之间的相等性（定理 7），这是一个理想化，因为物理状态无法被恢复如初。例如，free 把一块内存还给分配器，却不恢复 malloc 之前堆的布局；生成名（generative name）也不会被丢弃它的逆所恢复，因为下一次创建会取得一个新名 [39]。因此第 3 节的相等性要被读作在一个等价 ≃ 之下，且我们取 ≃ 为观测等价：两个状态在无观测者能区分它们时相关。比较行为而非表示是程序等价的既有途径 [40]，而这样的比较所产生的联系取决于观测者被给予什么来工作 [41]。上下文的观测者被给予的是它携带的余效应，每个余效应都自带等价（定义 24），因此上下文上的联系由它们的等价组装而成。组装它是本小节的事，而对其求商正是第 3.1.3 节所要求的独立性之来源。

定义 33. 两个余效应上下文在它们把相同的键绑定到相关的值时相关，两个上下文状态在其余效应投影相关时相关：

$$
\begin{array}{r c l} \sigma \simeq \sigma^ {\prime} & := & \mathrm{dom} (\sigma) = \mathrm{dom} (\sigma^ {\prime}) \wedge \forall k \in \mathrm{dom} (\sigma).   \sigma (k) \underset {k} {\simeq} \sigma^ {\prime} (k) \\ \gamma \simeq \gamma^ {\prime} & := & \sigma_ {\gamma} \simeq \sigma_ {\gamma^ {\prime}} \end{array}\tag{32}
$$

其中 $\sigma _ { \gamma }$ 表示 $\gamma$ 的余效应投影（定义 32）。

状态中没有任何键绑定的部分因此被遗忘，而遗忘它正是使定理 7 能够被读作 ≃ 之下的原因：上例中的堆布局和生成名位于该联系之外，除非某个键绑定它们。第 3.2.2 节对 ≃ 的需要是随之而来的而非被假设的。相关状态具有相同的定义域，因此它们在满足谓词 $\sigma \models d$ 和定义 $^ { 2 6 , }$ 的 notify 分类上一致，而响应性是 $\Sigma / \simeq$ 的性质。

把该联系称为观测的是关于每个 ${ \widetilde { \overline { { k } } } } ^ { \prime }$ 的断言，即它区分的不多于 k 的操作所能区分。值的观测者运行那些操作并读取其结果。

定义 34. 令 k 按定义 $^ { 2 4 , }$ 的意义携带操作集 A ，并写 ${ \mathfrak { M } } ( a )$ 为对每个参数 $x : X _ { a }$ 的效应函数 $a ( x )$ 的变换幺半群（定义 17）。A 上的测试是幺半群 ${ \mathfrak { M } } ( a ) , a \in { \mathcal { A } } ,$ 生成元上的有限词，每个字母应用于此前字母留下的值；其结果是在沿途正向映射为操作的字母所产生的那些，在前置条件失败处无定义。值 $v , v ^ { \prime } : V$ 不可区分，记作 $v \approx v ^ { \prime } .$ ，当 $A$ 上的每个测试在两者处都有定义或都没有定义，且在两者处产生相同的结果。

引理 35. 不可区分性是操作所尊重的最粗联系。即，

1. A 的每个操作按定义 24 的意义尊重 $\widetilde { \mathcal { A } }$ ；

2. A 的每个操作所尊重的每个等价都被包含在 ${ \widetilde { \widetilde { \lambda } } } ^ { \cdot }$ 中。$\widetilde { \overline { { k } } }$ 的每个可容许选择因此都被包含在 ${ \widetilde { \mathcal { A } } } _ { k } ^ { \prime }$ 中，且 $\widetilde { \mathcal { A } } _ { k }$ 本身可容许。

证明.

1. 令 v $\widetilde { \overline { { { A } } } } ^ { v ^ { \prime } }$ 并把 $a \in { \mathcal { A } }$ 应用于一个参数。用一字母作为测试前缀仍是一个测试，因此正向映射所达到的值不可区分，任何产生式逆从不可区分参数达到的值也不可区分；单字母测试给出两者的有定义性及结果的相等性。

2. 令 R 是这样一个等价且 $v R v ^ { \prime }$ 。测试的每个字母是操作的正向映射或产生的逆，而尊重关系沿两者携带 R，使所达到的值保持相关、每个字母处的结果保持相等。因此每个测试在 v 和 $v ^ { \prime }$ 处一致。 □

把 ≃ 代入 = 遍及全文本身并不足够，因为效应函数不仅返回状态还返回逆，而 ≃ 所等同的两个状态必须产生 ≃ 所等同的逆。

定义 36. 映射 $f : \Gamma \to \Gamma$ 尊重 ≃，当

$$
\forall \gamma , \gamma^ {\prime} \in \Gamma . \quad \gamma \simeq \gamma^ {\prime} \Rightarrow f (\gamma) \simeq f (\gamma^ {\prime})\tag{33}
$$

两个映射在它们在每个状态一致时相关，$\partial \Gamma$ 中的两个对在两个分量都相关时相关：

$$
\begin{array}{r c l} f \simeq g & := & \forall \gamma \in \Gamma . f (\gamma) \simeq g (\gamma) \\ (\delta , g) \simeq (\delta^ {\prime}, g ^ {\prime}) & := & \delta \simeq \delta^ {\prime} \wedge g \simeq g ^ {\prime} \end{array}\tag{34}
$$

尊重 ≃ 的映射是下降到 $\Gamma / \simeq ,$ 的映射，而由 ≃ 相关的两个映射是在那里下降到同一映射的两个。效应函数两者都需要：前者使其计算的状态在商上被确定，后者使其返回的逆如此。

定义 37. 把定义 8 读作 ≃ 之下：当 e 作为映射 $\Gamma \to \partial \Gamma$ 尊重 ≃，且对每个 $\gamma \in \Gamma$ 写作 $( \delta , g ) = e ( \gamma )$ 时

1. $g ( \delta ) \simeq \gamma ;$

2. $g$ 尊重 ≃。

则 $e \in { \mathfrak { E } } _ { \Gamma }$ 位于 ${ \mathfrak { E } } _ { \Gamma } ^ { * }$ 中。取 ≃ 为 Γ 上的相等性恢复定义 8。

引理 38. 按定义 $^ { 3 7 , }$ 读 ${ \mathfrak { E } } _ { \Gamma } ^ { * }$ 时，第 3.1 节断言的每个状态相等性在 = 替换为 $\simeq ,$ 后成立，且从 $( \gamma _ { 0 } , \mathrm { i d } _ { \Gamma } )$ 可达的每个状态的累加器尊重 $\simeq$

证明. 累加器是逆的复合，每个逆按定义 $3 7 ( 2 )$ 尊重 ≃，而尊重 ≃ 的映射的复合尊重 $\simeq ,$ 基例是 $\mathrm { i d } _ { \Gamma }$ 。第 3.1 节的证明随后原封不动地成立，尊重关系把联系穿过逆：由 $g _ { 2 } ( \delta _ { 2 } ) \simeq \delta _ { 1 }$ 和 $g _ { 1 } ( \delta _ { 1 } ) \simeq \gamma$ ，尊重关系给出 $( g _ { 1 } \circ g _ { 2 } ) ( \delta _ { 2 } ) \simeq \gamma ,$ ，即每次逆复合所采取的步骤，而定理 $7$ 的可靠性不变量由该步骤读作 $\varphi ( \gamma ) \simeq \gamma _ { 0 }$ □

定义 19 所要求的交换性由同一引理读作 ≃ 之下，而这样读它正是使它可达到的原因：两个操作可能留下 $\widetilde { \overline { { k } } }$ 所等同的值却仍算作交换。对两个操作，它要求比对其提升诱导的效应函数多一点东西，一个操作还产生结果。

定义 39. 操作 a 和 $a ^ { \prime }$ 是独立的，当它们的提升作为效应函数（定义 19）在每对参数处独立，且一方的变换不扰动另一方产生的结果：

$$
\forall x: X _ {a}, g \in \mathfrak {M} (a ^ {\prime \Sigma}), \sigma \in \Sigma . \quad \mathrm{pr} _ {3} (a ^ {\Sigma} (x) (g (\sigma))) = \mathrm{pr} _ {3} (a ^ {\Sigma} (x) (\sigma))\tag{35}
$$

交换 $a$ 和 $a ^ { \prime }$ 后同样成立，其中 ${ \mathfrak { M } } ( a ^ { \Sigma } )$ 表示对每个参数的提升 $a ^ { \Sigma } ( x )$ 的变换幺半群，如定义 34 对操作本身写 ${ \mathfrak { M } } ( a )$ 那样。键 k 是交换的，当 $\mathcal { A } _ { k }$ 的任意两个操作独立，操作与自身独立也包括在内。

跨不同键，该条件无条件成立。

定理 40. 不同键处的操作是独立的。

证明. 令 a 位于 $\mathcal { A } _ { k }$ 且 $a ^ { \prime }$ 位于 $\boldsymbol { A } _ { \boldsymbol { k } ^ { \prime } }$ ，其中 k $\neq k ^ { \prime }$ 。由定义 24，${ \mathfrak { M } } ( a ^ { \Sigma } )$ 的每个生成元具有 $\sigma \mapsto \sigma [ k \mapsto u ( \sigma ( k ) ) ]$ 的形式，其中 u 是 $\nu _ { k } ,$ 上的映射，它是正向映射的提升或产生逆的提升，$a ^ { \prime }$ 在 $k ^ { \prime }$ 处同理。两个这样的映射交换，每个只读写一个键且两个键不同，而引理 $1 8 ( 1 )$ 把交换性从生成元扩展到两个幺半群。对第二个条件，$a ^ { \Sigma }$ 在 $\sigma ,$ 处产生的东西（逆和结果都一样）由 $\sigma ( k )$ 决定，而 ${ \mathfrak { M } } ( a ^ { \prime \Sigma } )$ 的每个生成元保持其原样。□

值是由独立添加和移除的条目组成的表的键是交换的，路由或事件监听器的注册是代表情形：两次注册无论顺序如何都留下对每个测试应答相同的表，且任一注册都可以在另一注册在位时被撤出。值是有序链的键不是，因为插入到另一中间件之前的中间件会看到不同的请求，且任一顺序都不能在不扰动另一个的情况下被撤出。开篇示例的分配器按其接口发布的内容来划分。它所派发的句柄不被键的任何操作比较时，$\widetilde { \overline { { k } } }$ 可以把两个堆相关到句柄的重命名之下，这正是 CompCert 关联程序及其翻译的内存状态的方式 [42]，而分配是交换的；当地址是被相等性比较的结果时，没有可容许的 $\widetilde { \overline { { k } } }$ 使分配的两种顺序一致，且该键不是交换的。

组件执行的是操作的序列，其中每个操作可能依赖它之前的操作产生的东西，而该形状的效应函数正是下面定理所说的。

定义 41. 余效应中介的效应函数构成最小集 ${ \mathfrak { E } } _ { \Sigma } ^ { { \mathcal { A } } } \subseteq { \mathfrak { E } } _ { \Sigma }$ ，它包含单位 $\eta _ { \Sigma }$ 并在以下条件下封闭：对键 $k ,$ 操作 $a \in { \mathcal { A } } _ { k } ,$ 参数 x : $X _ { a } ,$ 和族 $\left( e _ { b } \right) _ { b \in B _ { a } }$ 的成员，

$$
\sigma \mapsto \mathbf {l e t} (\delta , s, b) = a ^ {\Sigma} (x) (\sigma) \mathbf {i n l e t} (\varepsilon , t) = e _ {b} (\delta) \mathbf {i n} (\varepsilon , s \circ t)\tag{36}
$$

又是一个成员。每个阶段执行一个操作并按结果选择其后续，因此参数可以依赖已获得的结果。成员中出现的操作是它的阶段所执行的，对所有结果选择。

定理 42. 令 $e _ { 1 } , e _ { 2 } \in \mathfrak { E } _ { \Sigma } ^ { \mathcal { A } }$ 且让两者的操作都出现的每个键都是交换的（定义 39）。则 $e _ { 1 }$ 和 $e _ { 2 }$ 独立（定义 19）。

证明. 对定义 41 的构造归纳，${ \mathfrak { M } } ( e _ { i } )$ 位于 $\boldsymbol { e } _ { i } { : }$ 中出现的操作的生成元所生成的子幺半群内：单位生成平凡幺半群，而阶段是 $a ^ { \Sigma } ( x )$ 与成员的 ⋄-复合，引理 18(2) 适用于它。

对定义 19 的条款 (1)，由引理 18(1) 只需 $e _ { 1 }$ 中出现的操作的生成元与 $e _ { 2 }$ 中出现的操作的生成元交换。两个操作位于不同键处时这是定理 $^ { 4 0 , }$ ，位于同一键处时该键携带两者的操作且按假设是交换的。

对条款 (2)，取 $g \in \mathfrak { M } ( e _ { 2 } )$ ，即 $e _ { 2 }$ 中出现的操作生成元的复合，并对 $e _ { 1 }$ 的构造归纳。单位在每个状态产生 $\mathrm { i d } _ { \Sigma }$ 。在一个阶段，令 $( \delta , s , b ) =$ $a ^ { \Sigma } ( x ) ( \sigma )$ 且 $( \varepsilon , t ) = e _ { b } ( \delta )$ ，则阶段在 $\sigma .$ 处产生 s ∘ t 。一次一个生成元地应用操作的独立性，在 $g ( \sigma )$ 处再次产生 s 和 t ，因此选择相同的续延 $e _ { b }$ ，而条款 (1) 把其运行的状态放在 $g ( \delta )$ ，归纳假设在那里再次产生 s 。因此阶段在 $g ( \sigma )$ 处产生 $s \circ t .$ □

组件与其环境的每次交互都穿过上下文，而类型族 K 不受约束，因此系统可以在自己的键处绑定它在组件间共享的每个位置（第 3.3.1 节）。组件的效应函数随后是沿余效应投影的余效应中介效应函数的提升，独立性转移到该提升，其变换只移动该投影。第 3.1.3 节留下的假设就这样被满足，随之而来的是整个组件系统的时间可组合性。

分解所划分的是计算的交换部分与其顺序敏感部分。交换部分由效应承载：组件按其任务要求的任何顺序执行它们，推论 21 按系统发现的任何方便的顺序逆转它们，没有两个组件互相约束。顺序敏感部分由余效应承载，因为操作不交换的键是其顺序必须由效应外部强加的键，而强加它有两个地方可用。在一个组件内由累加器强加，无论效应如何都按 LIFO 顺序逆转（定理 16）。在组件间由声明的余效应强加，一个组件提供另一个声明的东西，且提供先于声明的满足（第 3.2.2 节）。组合由此在组件的粒度上而非单个效应的粒度上达成，这正是第 4 节工作的尺度。

定理的两个限制值得指出。把每个共享位置绑定到键是范式的纪律而非构造的性质，因此系统不能具体化为余效应的位置位于第 6.1 节边界之外、随之也在定理之外。键的交换性是该键发布接口的性质，因此满足它是提供该键的组件的义务而非消费它的组件的义务。

## 3.3.3. 定位上下文范式（Situating the Context Paradigm）

编程范式在处理副作用的方式上根本不同。两个已确立的极点定义了该谱系：

显式状态传递（函数式）。为保持引用透明性，纯函数式语言把副作用建模为状态上的显式变换。State 单子 S → (S, S) [23] 把环境穿过每次计算。这种方法产生强组合保证：效应在类型中可见且适合等式推理。然而它带来显著的人机工程学代价：调用链中的每个函数都必须接受和返回状态参数，即使它只是原封不动地传递状态。随着效应维度数量的增长（日志、配置、I/O），单子栈或效应处理器样板不断增殖。

隐式变更（命令式/OOP）。主流命令式语言允许组件修改共享状态并在调用点无显式声明地访问依赖。在效应侧，代表例是 React 的 useEffect 钩子：它在组件内部纤维上注册一个持久副作用，但效应目标和注册机制都不作为显式参数出现——识别依赖隐藏运行时状态中调用顺序的位置。在余效应侧，Java 的服务定位器模式（例如 Spring 的 ApplicationContext.getBean(...)）在运行时从进程级注册表取回依赖，要求每个调用点做空检查和类型转换；依赖关系是隐式且分散在整个代码库中的。更一般地说，理解 f() 如何修改或依赖系统需要传递式地阅读其实现。重构变得脆弱，因为移动或移除调用可能静默破坏远处的依赖。

上下文范式结合了函数式方法的可追溯性与命令式方法的人机工程学。效应与余效应都通过显式上下文参数被中介。每个操作因此可归因于它被调用的特定上下文，进而归因于该上下文所属的组件。

除了结合两个极点的优势，上下文范式还让开发者单独处理每个效应和依赖，并自动把它们组合成系统的行为。对可逆效应，开发者提供每个原子操作的逆，而任何复合的逆通过组合而得到（第 3.1 节），因此组件的拆卸由加载推导而来而非与之并列书写。对响应式余效应，组件只声明它需要的依赖，运行时自动解析和重连它们（第 3.2 节），在提供者被添加、移除或替换时保持它们一致接线。在两个方向上，原本依赖开发者纪律的正确性成为范式的结构性质。

## 4. 动态组合演算（A Calculus of Dynamic Composition）

第 3 节仅在局部形式确立了空间与时间可组合性。把它们推广到整个系统需要把系统分解为组件，每个组件把一个余效应规范与一个带见证的效应函数配对，从而使与共享环境的每次交互都可归因于其中一个。以下各节给这种分解配以操作语义，并确立其全局形式的空间与时间可组合性。

第 4.1 节和第 4.2 节给出能赋予生命周期规则的最小演算，它把每个转移视为原子的、即时的且不会失败的；第 4.3 节放弃这三个假设，原子性按转移可能运行的方向各抛弃一次，容纳运行时在转移开始与结束之间插入的控制流形式，得到真实运行时实现的演算；第 4.4 节确立该演算的元理论，即保真、全局时间与空间可组合性、进展性和合流性。

## 4.1. 组件与纤维（Components and Fibers）

本节固定规则作用的对象：组件；纤维，即携带自身生命周期状态的组件实例化；以及注册表（registry），它承载状态携带的纤维，余效应上下文从中读出。

组件。组件以三元组给出，其余效应侧被拆分为它从环境读取的东西与它向环境提供的东西。

定义 43. 上下文 Γ 上的组件（同时携带效应与余效应，定义 32）定义为：

$$
\mathfrak {C} _ {\Gamma} := \mathfrak {D} _ {\Gamma} \times \mathfrak {P} _ {\Gamma} \times \mathfrak {E} _ {\Gamma} ^ {*}\tag{37}
$$

表示三元组 $( d , p , e )$ ，其中：

$d : { \mathfrak { D } } _ { \Gamma }$ 是定义 25 的余效应规范，声明从环境要求的依赖；

$p : \mathfrak { P } _ { \Gamma } : = \mathsf { S e t } ( K )$ 是提供（provision），声明组件可能提供的余效应键，且 p 之外的键不是其效应函数写入的键；

$e : { \mathfrak { E } } _ { \Gamma } ^ { * }$ 是定义 8 的带见证效应函数，定义组件激活时贡献的效应以及撤出它们的逆。

两个声明是一个接口的两个方向，d 是组件从环境读取的东西，p 是组件向环境写入的东西，而第 4.2 节不允许一个注册表中两个提供相交的纤维。下标在全文对 Γ 取，余效应上下文是其投影之一（定义 32），因此定义 25 的 $\mathfrak { D } _ { \Sigma }$ 此处写作 $\mathfrak { D } _ { \Gamma }$。

提供的两两不相交是本章与第 3.2.3 节分手之处。定义 28 的隔离让一个键穿过领域表解析，因此两个纤维可以在不同领域中提供同一个键；携带领域的演算会把不相交性放松为领域内的不相交性，并会针对声明纤维的领域解析声明键。我们不在此引入领域，而是在一个共享领域读出每个键，这使上述不相交性是正确条件、每个键的提供者唯一（定义 45）。它限制的是一个组件被实例化的频率：提供非空的组件每次只有一个纤维，因此下面的多次实例化都是不提供任何东西的组件——这是只消费或注册其他组件的组件的常见情形。

运行系统中实例化的组件会随时间被激活和停用，因此它携带生命周期状态，而转移是把它从一个生命周期状态移动到另一个：激活执行 $e ,$ 在上下文中累积副作用，停用应用累加器以恢复上下文。在最简形式下，生命周期是图 1 的两状态模型，第 4.2 节为其给出规则；第 4.3 节在容纳每种控制流特性时对其精化。

![](images/04c2ce355a1ac2d664aa3f8258048f472676b9b8af70faecb64e857f85d09a02.jpg)  
图 1 | 基础组件生命周期

纤维。一个组件可以被实例化多次，每次实例化携带自己的生命周期状态。我们把这样的实例化命名为纤维。纤维记录产生它的组件、它被实例化所在的纤维、它提供的余效应，以及它处于生命周期的何处。

定义 44. 固定纤维名集合 N。实例化组件 $( d , p , e ) \in \mathfrak { C } _ { \Gamma }$ 的纤维是元组 $\langle d , p , e , \pi , \sigma , \tau , \theta \rangle$ ，其中

$d : \mathfrak { D } _ { \Gamma } , p : \mathfrak { P } _ { \Gamma }$ 和 $e : { \mathfrak { E } } _ { \Gamma } ^ { * }$ 是定义 43 的余效应规范、提供和效应函数；

• π : N ∪ {root} 是父纤维，即此纤维被实例化所在的纤维，或根标记 root；

• σ : Σ 是纤维自身的余效应表（定义 22），激活前为空，由运行的效应写入；

$\tau : \{ \bot , \top \}$ 是退役标志，新纤维中为 ⊥，编排器已退役纤维后为 ⊤；

$\theta : \Theta _ { \Gamma }$ 是生命周期状态，在第 4.2 节的两状态模型下为

$$
\Theta_ {\Gamma} := \text { Inactive } \mid \text { Active } (g, \omega)\tag{38}
$$

其中 $g : \Gamma \to \Gamma$ 是累加器，ω : d → N 是已提交视图（committed view）。

已提交视图 $\omega$ 把纤维声明的每个键发送到转移提交时提供它的纤维的名字。第 4.3 节用进行中转移所需的扩展替换 $\Theta _ { \Gamma }$ ；定义 44 的其余部分对两者一次性给出，仅 ω 在第 4.3 节各层引入的更丰富效应类型处读出。

注册表。状态在名字下持有其纤维，而纤维的身份与第 3.2 节的余效应上下文都从该安排中读出。

定义 45. 写 $\mathfrak { F } _ { \Gamma }$ 为 Γ 上纤维的集合。状态 $\gamma \in \Gamma$ 携带注册表

$$
F _ {\gamma}: \mathfrak {N} \rightharpoonup \mathfrak {F} _ {\Gamma}\tag{39}
$$

一个有限部分函数，其父指针形成以 root 为根的树，连同 Γ 中任何纤维的 $\sigma$ 都不命名的其余部分。我们写 $\gamma ( n )$ 表示 $F _ { \gamma } ( n )$ ，并在状态清晰时用 n 下标缩写 $\gamma ( n )$ 的字段，因此 $d _ { n } , p _ { n } , e _ { n } , \pi _ { n } , \sigma _ { n } , \tau _ { n } , \theta _ { n }$ 是定义 44 的字段，$g _ { n } , \omega _ { n }$ 是 $\theta _ { n }$ 携带的累加器和已提交视图；$\gamma [ \theta _ { n } \mapsto \theta ^ { \prime } ]$ 、γ[n ↦ $\langle \cdots \rangle ]$ 和 $\gamma \setminus n$ 分别是与 $\gamma$ 在一个字段、一个纤维和有一个纤维在场这三方面不同的状态。

纤维的名字赋予它一个在其自身变更中存活的身份：下面的每个规则都重写一个纤维的生命周期状态而让其他纤维独处，因此规则必须说明是哪一个，而两个字段引用纤维而非描述它们，即父 π 和已提交视图 ω。名字是原子：没有规则计算一个名字、检查其结构或用相等性以外的任何方式关联两个名字，引入纤维只是抽取一个未使用的名字。这是动态创建的局部名字的纪律 [39]，此处用于纤维身份。

每个纤维拥有一个表意味着余效应上下文是派生的而非存储的：它是活动纤维共同提供的东西。

$$
\sigma_ {\gamma} := \bigcup \left\{\sigma_ {m} \mid m \in \operatorname{dom} \left(F _ {\gamma}\right), \theta_ {m} = \text { Active } (-, -) \right\}\tag{40}
$$

该并集良定义，因为纤维只写它声明的键，dom $( \sigma _ { n } ) \subseteq p _ { n } .$ 且不同纤维的提供不相交（定义 43），因此每个 $k \in \mathrm { d o m } ( \sigma _ { \gamma } )$ 恰好位于一个 Active 纤维的表中，其名字我们写为 provide $\Phi _ { k } ( \gamma ) \in \mathfrak { N }$ 并称其为 k 的提供者。每个键因此只有一个可能的提供者，由提供决定而非由状态决定。没有规则直接写 $\sigma _ { n }$ ：纤维的提供是它自己的效应函数执行的集合运算，这些运算落在 $\sigma _ { n }$ 中因此已经是 $e _ { n }$ 返回状态的一部分，并随累加器一起离开。只有效应的余效应部分以此方式记录，因为只有余效应部分是其他纤维所声明的；在 γ 的其他地方改变状态的效应像任何其他效应一样由 e 跟踪，但没有纤维能在规范中命名它们，因此它们不贡献排序约束。

第 3.2.2 节的满足关系随后原样适用，以 $\gamma \models d$ 缩写 $\sigma _ { \gamma }$ ⊧ d。键位于 dom $\left( \sigma _ { \gamma } \right)$ 当且仅当某个 Active 纤维安装了它，其提供是它可以安装的键而非已安装的键，因此 $\gamma ^ { \textsf { k } }$ ⊧ d 已经要求每个声明键有 Active 提供者。只对 Active 纤维取并集使纤维能在未撤出任何东西前停止提供，第 4.3.1 节把这变成排序纪律。

## 4.2. 基础演算（The Base Calculus）

本节只给出图 1 的两状态生命周期的演算：每个纤维与之比较的目标，以及移动它的五个规则。

目标视图。规则把每个纤维与目标比较，即它是否应当运行以及针对其依赖的哪个解析。目标不是纤维单独的性质，因为纤维声明的键针对整个状态解析，所以它是该状态上的谓词。

定义 46. n 在 γ 处的目标视图把每个声明键映射到其提供者，因此是总映射 $d _ { n } \to \mathfrak { N }$ ，当 n 根本不该运行时为 ⊥：

$$
\operatorname{target} _ {n} (\gamma) := \left\{ \begin{array}{l l} \bot & \text {if} \tau_ {n} \lor \neg (\gamma \vDash d _ {n}) \\ (k \in d _ {n}) \mapsto \operatorname{provider} _ {k} (\gamma) & \text {otherwise} \end{array} \right.\tag{41}
$$

当每个纤维都达到其目标视图时，状态是静止的（quiescent）：

$$
\operatorname{quiet} (\gamma) := \forall n \in \operatorname{dom} \bigl (F _ {\gamma} \bigr). \left\{ \begin{array}{l l} \operatorname{target} _ {n} (\gamma) = \bot & \text {if} \theta_ {n} = \mathsf {I n a c t i v e} \\ \operatorname{target} _ {n} (\gamma) = \omega_ {n} & \text {if} \theta_ {n} = \mathsf {A c t i v e} (-, \omega_ {n}) \end{array} \right.\tag{42}
$$

目标只应答两件事而不应答别的：通过 $\tau _ { n } ,$ 退役，以及通过 γ ⊧ $d _ { n }$ 和 provide $\mathrm { r } _ { k } ,$ 余效应解析，每个声明键在定义 43 的一个共享领域处从 $\sigma _ { \gamma }$ 读出。

定义 44 的已提交视图与目标视图同类型，而生命周期由比较它们驱动：$\omega _ { n }$ 是 n 针对其激活的解析，$\mathrm { t a r g e t } _ { n } ( \gamma )$ 是它应针对其运行的解析，下面的每个规则都因它们一致或不一致而触发。记录提供者而非值是使比较可用之处，因为提供相等值的不同纤维否则会比较相等。组件读取的值通过视图达到，因为提供者的表持有该值，而实现把该映射保存在 fiber.committed 中、把其哈希保存在 fiber.target 中（第 5.1.3 节）。

规则。基础演算把每个转移视为原子的、即时的且不会失败的：激活一步应用其效应函数，停用一步应用累加器，两者都成功。第 4.3 节放弃全部三个。

五个规则生成两个关系。编排规则，前缀 O-，写作 $\gamma \Rightarrow \delta ,$ 是编排器可执行的动作；其前提说明动作何时合法，而非何时发生。生命周期规则，前缀 L-，写作 $\gamma \longrightarrow \delta ,$ 是系统在其前提成立时主动采取的步骤。步骤序列交错这两者，下面的 $\stackrel { * } {  }$ 仅指生命周期步骤。

$$
\begin{array}{c} \frac {n \notin \operatorname{dom} (F _ {\gamma}) \quad \pi \in \operatorname{dom} (F _ {\gamma}) \cup \{\text {root} \} \quad (d , p , e) \in \mathfrak {C} _ {\Gamma} \quad \forall m \in \operatorname{dom} (F _ {\gamma}) .   p \cap p _ {m} = \varnothing}{\gamma \Rightarrow \gamma [ n \mapsto \langle d , p , e , \pi , \varnothing , \bot , \text {Inactive} \rangle ]} \text {O - Insert} \\ \frac {n \in \operatorname{dom} (F _ {\gamma})}{\gamma \Rightarrow \gamma [ \tau_ {n} \mapsto \top ]} \text {O - Retire} \\ \frac {\tau_ {n} = \top \quad \theta_ {n} = \text {Inactive} \quad \forall m .   \pi_ {m} \neq n}{\gamma \Rightarrow \gamma \setminus n} \text {O - Remove} \end{array}
$$

插入和退役是仅有的外部输入：编排器要求一个纤维存在或停止存在，绝不直接设置其生命周期状态。O-Retire 对纤维状态无条件，因为退役是一个请求，而生命周期规则负责执行它。退役与移除分离出于同样原因：仍 Active 的退役纤维必须首先被停用，过早移除会丢弃累加器并泄漏。前提 ∀m. $\pi _ { m } \neq$ n 通过在移除其父之前移除子节点来保持树良构。O-Insert 的最后一个前提是施加单一来源纪律之处：一个键只有一个可能的提供者，因为编排器不能接纳声明它的第二个组件。

$$
\begin{array}{c} \frac {\theta_ {n} = \text {Inactive} \quad \omega = \text {target} _ {n} (\gamma) \neq \bot \quad e _ {n} (\gamma) = (\delta , g)}{\gamma \longrightarrow \delta [ \theta_ {n} \mapsto \text {Active} (g , \omega) ]} \text {L - Reload} \\ \frac {\theta_ {n} = \text {Active} (g , \omega) \quad \text {target} _ {n} (\gamma) \neq \omega \quad g (\gamma) = \delta}{\gamma \longrightarrow \delta [ \theta_ {n} \mapsto \text {Inactive} ]} \text {L -Unload} \end{array}
$$

L-Reload 把已提交视图与逆一起安装；L-Unload 应用逆并丢弃已提交视图。两者由同一比较驱动：L-Reload 在纤维不持有已提交视图且其目标视图非 ⊥ 时触发，L-Unload 在它持有的已提交视图非其目标视图时触发。这是第 3.2 节的响应式纪律，针对既应答退役也应答余效应的目标读出：每当目标视图改变时启动转移，无论两者中哪一个移动了它。

实例化。组件在安装其效应时可以实例化另一个组件，这正是插件宿主在插件加载自己的插件时所做的。到目前为止的规则把注册表留给编排规则单独处理，因此这样的实例化无处发生。一个原语给了它地方。

定义 47. $\boldsymbol { e } _ { n }$ 的应用，或第 4.3.2 节适用处其迭代之一，可以注册组件 $( d , p , e ) \in \mathfrak { C } _ { \Gamma }$ 。它代替状态映射取该组件以 $\pi = n$ 的 O-Insert，并把该纤维的 O-Retire 作为其逆产出。规则抽取名字（受 O-Insert 的新鲜性前提约束）并交给效应函数。

逆退役而非移除，原因是逆必须能在其到达的任何地方应用。O-Remove 携带前提，因此由它构建的逆可能失败：父仍 Active 的子组件无法运行其累加器，且没有规则会移动该子组件，因为定义 46 不读纤维树。O-Retire 唯一的前提是 $n \in \mathop { \mathrm { d o m } } \mathop { \left( F _ { \gamma } \right) }$ 。它在注册被提取的状态留下的条目是已退役的，Inactive(⊥)，并持有空表，即引理 $5 7 { : }$ 的残余条目（vestigial entry）：它仅在控制字段上不同于纤维的缺席，且没有规则能区分两者。

退役子组件设置 τ 从而使其目标视图变为 ⊥，此后普通规则把它带回 Inactive。父组件不被要求等待，O-Retire 无条件，因此 L-Unload 无论子组件是否离开都适用于父组件。孙组件一次一级到达，子组件自己的累加器退役子组件注册的东西。定理 66 连同第 4.3.1 节沿余效应施加的级联一起覆盖该级联。

约束（Confinement）。手握这一个例外，效应函数所受的纪律可以给出。它限制一次应用写什么，使应用它的规则能说明每次其他变化，并限制一次应用读什么，使纤维看到它声明的余效应而不多看到注册表。限制写入是第 4.4 节把表 1 读作它们的完整清单的依据。

定义 48. 映射 $f : \Gamma \to \Gamma$ 对 n 是约束的，当对每个满足 $n \in \mathop { \mathrm { d o m } } \mathop { \left( F _ { \gamma } \right) }$ 的 $\gamma \in \Gamma$ ，写作 $\delta = f ( \gamma )$ 11

1. （写入）dom $( F _ { \delta } ) = \mathrm { d o m } \big ( F _ { \gamma } \big ) , \delta ( m ) = \gamma ( m )$ 对每个满足 m $\neq n ,$ 的 $m \in \mathop { \mathrm { d o m } } \bigl ( F _ { \gamma } \bigr )$ ，且 $\delta ( n )$ 和 $\gamma ( n )$ 仅 θ 不同；

2. （读取）在 $\sigma _ { n } ,$ 上、在对每个 $m \in \mathop { \mathrm { d o m } } \bigl ( F _ { \gamma } \bigr )$ 的限制 $\sigma _ { m } | _ { d _ { n } }$ 上、以及在无纤维表命名的状态部分上一致的两个状态被 f 带到在同样三样上一致的状态。

效应函数 e 对 n 是约束的，当它的每次应用、以及第 4.3.2 节适用处它的每次迭代，要么注册一个组件（定义 47），要么其状态映射 $\mathrm { p r } _ { 1 } \circ e$ 和它产生的逆都对 n 约束。每个纤维的效应函数被要求对该纤维约束。

注册写入 O-Insert 写入的条目，在它抽取的唯一位名字处，别无其他；它作为逆产出的 O-Retire 只写该名字的 θ，别无其他。两种应用因此都不写已在场纤维的控制字段（除该 θ 外），且完全不读取。

条款 (2) 是组件能读取其声明值的原因：那些值位于其提供者的表中，因此不读任何表（除 $\sigma _ { n }$ 外）的效应函数将无法使用自己的余效应。它不能读的是 $d _ { n } ,$ 之外的表或任何控制字段，这使组件不能分支于它未声明的纤维的生命周期状态。

规则是非确定性的：多个纤维可能持有与其目标视图不同的已提交视图，而该联系不承诺它们之间的顺序。它们也只具响应性，没有规则提及调度器；步骤是任意规则应用序列，因此在所有此类序列上证明的定理对运行时可能采用的每个调度策略都成立。

## 4.3. 进行中的转移（Transitions in Progress）

本节在四种设定下扩展基础演算。第一种提供第 3.2 节要求而第 4.2 节无法表达的东西——一个其依赖方可占用的区间上展开的停用；其余三种放弃转移是原子的、即时的且不会失败这一理想化，真实运行时中的转移三者皆非。被放弃的是整个转移是一步，而非一步是一次规则应用，而四种共享一个结构性后果，在此一次性处理：非一步的转移需要在其进行期间占据一个状态，每个可能运行的方向一个。

定义 49. 本节的生命周期状态把 $\Theta _ { \Gamma }$ 替换为

$$
\Theta_ {\Gamma} := \text { Inactive } (\zeta) \mid \text { Reloading } (i, g, \omega) \mid \text { Active } (g, \omega) \mid \text { Unloading } (g, \omega , \zeta)\tag{43}
$$

其中 $i : \mathfrak { E } _ { \Gamma } ^ { \mathrm { i t e r * } }$ 是剩余效应迭代器（下面的定义 51），$g : \Gamma \to \Gamma$ 是迄今构建的累加器，$\omega : d  \mathfrak { N }$ 是已提交视图，$\zeta : \{ \bot \} \cup \Xi$ 是结果，由 Unloading 携带作为其停用所指向的结果，由 Inactive 携带作为它所达到的结果，要么 ⊥，要么从第 4.3.4 节提供的错误集 $\Xi$ 抽取的错误。

纤维在处于三个携带累加器和已提交视图的状态之一时是已安装的（installed），在携带错误结果时是失败的（failed）：

$$
\operatorname{installed} _ {n} (\gamma) := \theta_ {n} \neq \operatorname{Inactive} (-), \quad \text {   failed   } _ {n} (\gamma) := \exists \xi \in \Xi . \theta_ {n} = \operatorname{Inactive} (\xi)\tag{44}
$$

已安装纤维 n 把 k 解析为 m，当 $\omega _ { n } ( k ) = m .$ 。定义 46 的静止性在更宽的状态空间上读作

$$
\operatorname{quiet} (\gamma) := \forall n \in \operatorname{dom} \bigl (F _ {\gamma} \bigr). \left\{ \begin{array}{l l} \zeta \neq \bot \lor \operatorname{target} _ {n} (\gamma) = \bot & \text {if} \theta_ {n} = \operatorname{Inactive} (\zeta) \\ \operatorname{target} _ {n} (\gamma) = \omega_ {n} & \text {if} \theta_ {n} = \operatorname{Active} (-, \omega_ {n}) \\ \bot & \text {otherwise} \end{array} \right.\tag{45}
$$

第 4.1 节的定义延续到这个状态空间，有两个读法需要固定。首先，第 4.2 节的 Inactive 在 O-Insert 的结论中读作 Inactive(⊥)、在 O-Remove 的前提中读作 Inactive $( - )$ 。其次，$\sigma _ { \gamma }$ 仍只并集 Active 纤维的表，因此转移任一个方向进行中的纤维通过它持有的 $\omega$ 读取其余效应，且不提供自己的余效应；其转移已写入的键因此还不是依赖方可据以激活的键。在两状态演算中该区分是空洞的，那里每个已安装纤维都是 Active。

图 2 画出这些状态形成的生命周期，下面四个小节在其边上提供规则。

![](images/292085ac3f4ef886f94c611c14a57c3de3fd5a92462c7a5892130e190975f400.jpg)  
图 2 | 带进行中转移的生命周期；两个转移状态被描出轮廓

## 4.3.1. 撤出（Withdrawal）

第 3.2 节要求依赖方在其依赖之后激活，且依赖方只在其依赖方已停用后才撤出其提供。前半在基础演算中已经成立：激活要求 $\gamma \models d _ { n } ,$ 因此声明 d 的纤维不能在某个纤维正提供 k 之前激活。后半是实质性的，它必须交付的不只是状态变化的排序。因提供者将消失而被拆除的组件正运行其自身的拆卸代码，而它可能需要正被撤出的余效应本身；关闭连接池通常意味着把连接还给提供它们的人。后半必须交付的是消费者在其自身停用期间仍能读取 k，且提供者对 k 的撤出只在其后生效。基础演算根本无法交付：其 L-Unload 同时移除提供并运行逆，在两者之间不给消费者的拆卸留下区间。

本层把这一步拆成两步，并用以下条件守卫后半。

定义 50. 当某个其他已安装纤维把一个键解析到它时，纤维 n 在 γ 处被依赖（relied）：

$$
\begin{array}{c} \operatorname{relied} _ {n} (\gamma) := \exists m \in \operatorname{dom} \bigl (F _ {\gamma} \bigr), k \in d _ {m}. m \neq n \wedge \operatorname{installed} _ {m} (\gamma) \wedge \omega_ {m} (k) = n \\ \frac {\theta_ {n} = \mathsf {A c t i v e} (g , \omega) \quad \operatorname{target} _ {n} (\gamma) \neq \omega}{\gamma \longrightarrow \gamma [ \theta_ {n} \mapsto \mathsf {U n l o a d i n g} (g , \omega , \bot) ]} \text {L - Leave} \\ \frac {\theta_ {n} = \mathsf {U n l o a d i n g} (g , \omega , \zeta) \quad \neg \operatorname{relied} _ {n} (\gamma) \quad g (\gamma) = \delta}{\gamma \longrightarrow \delta [ \theta_ {n} \mapsto \mathsf {I n a c t i v e} (\zeta) ]} \text {L - Unload} \end{array}\tag{46}
$$

L-Leave 记录停用决定而不对其行动，这使纤维停止提供其余效应，同时保持它自己的已提交视图和别人的已提交视图原封不动。L-Unload 应用累加器、丢弃已提交视图并使纤维以其携带的结果停在 Inactive；结果在 4.3.4 节提供另一种情形前为 ⊥。它是演算中唯一应用累加器的规则。

排序的两半随后由形式的不同部分承载：可见性一半由已提交视图承载，L-Unload 作为其最后行动丢弃它；排序一半由前提 ¬ relied (n) 承载，我们称之为守卫，它把 n 的撤出推迟到每个把它解析为 n 的消费者都离开。定理 63 确立两者。

守卫按绑定而非按纤维施加：relied $_ n ( \gamma )$ 测试某个已提交视图是否命名 $n ,$ 因此不声明 n 的任何键的纤维不是障碍，在另一个领域（第 3.2.3 节）解析 $n \mathrm { { 's } }$ 的键的纤维也不是。在第 4.2 节的单一来源纪律下，按绑定读法恰与更粗的测试 ∃m ≠ n, $k \in$ $d _ { m }$ 。在 ${ \mathrm { s t a l l e d } } _ { m } ( \gamma ) \wedge k \in p _ { n } .$ 重合，键在那里只有一个可能的提供者。

此类守卫通常会死锁。使它不死锁的是 Unloading 与 $\sigma _ { \gamma }$ 只并集 Active 纤维：一旦 L-Leave 标记了 $n ,$ 其表离开 $\sigma _ { \gamma } ,$ 因此没有目标视图能再命名 n，而每个承诺给 n 的消费者本身已在退出之路上。定理 66 把它转化为守卫总是释放的断言。

守卫沿余效应而非沿纤维树对停用排序：父组件可以在其子组件仍 Unloading 时运行其逆，因为 relied 只谈论已提交视图。父与子相应地比定理 63 对提供者与其消费者排序得更弱，而在环境状态中效应相交的父与子由定义 60 的独立性假设管辖。

## 4.3.2. 迭代（Iteration）

激活可以按顺序执行多个效应，而停用必须恢复它们。我们用效应迭代器建模这样的激活，其每次迭代产生修改后的上下文、一个逆和一个续延：

定义 51. 定义效应迭代器 ${ \mathfrak { E } } _ { \Gamma } ^ { \mathrm { i t e r } }$ 和带见证的效应迭代器 $\mathfrak { E } _ { \Gamma } ^ { \mathrm { i t e r * } }$ 为如下递归类型：

$$
\begin{array}{c} \mathfrak {E} _ {\Gamma} ^ {\text {iter}} := \mu \mathfrak {I}.   \Gamma \to \Gamma \times (\Gamma \to \Gamma) \times \text {Maybe} (\mathfrak {I}) \\ \mathfrak {E} _ {\Gamma} ^ {\text {iter*}} := \mu \mathfrak {I}.   (e: \Gamma \to \Gamma \times (\Gamma \to \Gamma) \times \text {Maybe} (\mathfrak {I})) \\ \qquad \qquad \qquad \qquad \times ((\gamma : \Gamma) \to (\textbf {l e t} (\delta , g, o) = e (\gamma)   \textbf {i n} g (\delta) \simeq \gamma)) \end{array}\tag{47}
$$

其中 $e ( \gamma )$ 产生三元组 $( \delta , g , o )$ 表示：

• $\delta$ 是新的上下文；

• $g$ 是当前效应的逆函数；

• o 表示续延：

‣ Nothing 表示迭代终止；

‣ Just(i) 提供下一次迭代。

见证在定义 33 的 ≃ 处读出，正如定义 37 读 ${ \mathfrak { E } } _ { \Gamma } ^ { * }$ 的见证：当 i 尊重 ≃ 且它产生的每个 $g$ 尊重 ≃ 并满足上述条款时，$i \in { \mathfrak { E } } _ { \Gamma } ^ { \mathrm { i t e r } }$ 位于 ${ \mathfrak { E } } _ { \Gamma } ^ { \mathrm { i t e r * } }$ 中。三元组逐分量比较，Nothing 只与 Nothing 比较，Just(i) 在 $i \simeq i ^ { \prime }$ 时与 Just $( i ^ { \prime } )$ 比较，而迭代器上的 $\simeq \mathrm { o n }$ 是满足这些条款的最大联系。取 ≃ 为 Γ 上的相等性精确恢复该读法。

效应迭代器变换 $\mathrm { e f f e c t } ^ { \mathrm { i t e r } } _ { \Gamma }$ 通过递归调用把 $\mathrm { e f f e c t } _ { \Gamma }$ 扩展到迭代器结构：

定义 52. 定义效应迭代器变换 $\mathrm { e f f e c t } ^ { \mathrm { i t e r } } _ { \Gamma }$ 为：

$$
\begin{array}{r c l} \text {effect} _ {\Gamma} ^ {\text {iter}} & : & \mathfrak {C} _ {\Gamma} ^ {\text {iter}} \to \partial \Gamma \to \partial^ {2} \Gamma \\ & & \text {let} (\delta , g, o) = i (\gamma) \text {in} \\ & & \text {let} t = \text {track} _ {\Gamma} (g, \text {pr} _ {1} \circ i) \text {in} \\ \text {effect} _ {\Gamma} ^ {\text {iter}} & = & i \mapsto (\gamma , \varphi) \mapsto \begin{array}{c} \textbf {m a t c h} o \\ | \text {Nothing} \Rightarrow ((\delta , \varphi \circ g), t) \\ | \text {Just} (i ^ {\prime}) \Rightarrow \text {let} (s, r) = \text {effect} _ {\Gamma} ^ {\text {iter}} (i ^ {\prime}) (\delta , \varphi \circ g) \text {in} \\ (s, t \circ r) \end{array} \end{array}\tag{48}
$$

在每次迭代，逆 $g$ 按应用顺序复合到 $\varphi ,$ 上，因此累加器 $\varphi \circ g _ { 1 } \circ \cdots \circ g _ { k }$ 应用时自然按 LIFO 顺序恢复效应。由于 $\mathrm { e f f e c t } _ { \Gamma } ^ { \mathrm { i t e r } }$ 落在与 $\mathrm { e f f e c t } _ { \Gamma }$ 相同的 $\partial \Gamma  \partial ^ { 2 } \Gamma$ 中，迭代器本身就是一个效应，可用于任何效应可用之处。组件的一次完整激活就是这样一个使用，这正是本节其余部分形式化的东西，而实现在每个变更处接纳迭代器（第 5.1.1 节）。$\mathsf { M a y b e } ( \mathfrak { E } ^ { \mathrm { i t e r } } )$ 续延使任意两个连续迭代之间有一个边界可用，在该边界处上下文是迭代至今所制造的样子，累加器恢复它们而不恢复更多。在这个意义上，效应迭代器是具体化的限定续延，即主流语言通过 yield 运算符暴露的结构 [43]，因此该模型直接映射到它们已提供的生成器上。

在演算中，定义 44 的 $e _ { n }$ 从此刻起在 $\mathfrak { E } _ { \Gamma } ^ { \mathrm { i t e r * } }$ 处读出，用迭代器替换原子效应函数把基础 L-Reload 拆成一个迹所穿过的开始状态，并给纤维第二个离开该状态的出口。

$$
\begin{array}{c} \frac {\theta_ {n} = \text {Inactive} (\bot) \quad \omega = \text {target} _ {n} (\gamma) \neq \bot}{\gamma \longrightarrow \gamma [ \theta_ {n} \mapsto \text {Reloading} (e _ {n} , \text {id} _ {\Gamma} , \omega) ]} \text {L - Begin} \\ \frac {\theta_ {n} = \text {Reloading} (i , g , \omega) \quad \text {target} _ {n} (\gamma) \neq \omega \quad (\delta , h) = (\gamma , \text {id} _ {\Gamma}) \lor i (\gamma) = (\delta , h , -)}{\gamma \longrightarrow \delta [ \theta_ {n} \mapsto \text {Unloading} (g \circ h , \omega , \bot) ]} \text {L - Divert} \\ \frac {\theta_ {n} = \text {Reloading} (i , g , \omega) \quad \text {target} _ {n} (\gamma) = \omega \quad i (\gamma) = (\delta , h , \text {Just} (i ^ {\prime}))}{\gamma \longrightarrow \delta [ \theta_ {n} \mapsto \text {Reloading} (i ^ {\prime} , g \circ h , \omega) ]} \text {L - Iter} \\ \frac {\theta_ {n} = \text {Reloading} (i , g , \omega) \quad \text {target} _ {n} (\gamma) = \omega \quad i (\gamma) = (\delta , h , \text {Nothing})}{\gamma \longrightarrow \delta [ \theta_ {n} \mapsto \text {Active} (g \circ h , \omega) ]} \text {L - Finish} \end{array}
$$

每次迭代把新产生的逆作为 ${ \boldsymbol { g } } \circ { \boldsymbol { h } } ,$ 复合到累加器上，遵循定义 52，使累加器按后进先出顺序应用逆。任意两个连续迭代之间，系统可以在其目标视图已改变时使转移转向，应用迄今累积的逆以恢复上下文。L-Divert 像每个其他停用一样经 Unloading 路由而非就地应用累加器，且它在那里遇到的守卫是空洞的，从未 Active 的纤维不提供任何东西也不出现在任何已提交视图中。其两个备选中的第一个中止纤维持有的迭代，这只有迭代边界才使之可能，因此转向可落在的粒度是迭代器的粒度；第二个让该迭代落地，第 4.3.3 节是它被需要之处。

普通效应函数 $( { \mathfrak { E } } _ { \Gamma } )$ 是第一次迭代已产生 Nothing 的退化情形。这样的转移仍穿过 Reloading，L-Divert 仍在那里适用，但累加器是 $\mathrm { i d } _ { \Gamma }$ 且没有迭代运行，因此没有恢复任何东西，而转移要么安装其全部效应要么完全不安装。

## 4.3.3. 异步（Asynchrony）

迄今的各层让环境在一次迭代与下一次之间移动，并假设每次迭代本身瞬时完成，其启动和落地是一步。我们抽象地建模非即时性：迭代产生 Future(A) 类型的值，其中 Future 是不透明类型构造器，其定义性质是提交与解析之间外部状态可能改变。

在此模型下，迭代在一个状态启动、在另一个状态落地，而纤维在飞行期间是 Unloading。本层增加的是惯性（inertia）：一旦启动，迭代落地，且其落地不能被拒绝。飞行期间转向的目标视图因此不能通过中止迭代来应答，只剩下 L-Divert 中落地一个迭代的备选可用：迭代落地，纤维随后停用。本层因此不增加规则，也不增加规则匹配的类型；在 Γ 的粒度上惯性是它的全部内容，它采取的形式是对宿主可取 L-Divert 哪个备选的限制。

那个备选是基础演算无法表达的。那里，目标视图已转向的转移在发现它的同一步被撤销；这里飞行中的迭代必须先落地，因此纤维需要在逆运行时有处可待，唯一可靠的地方是持有迭代产生的逆的 Unloading。经 Active 路由会让纤维提供其余效应达一步之长，并使其依赖方针对已离开的组件激活。这就是实现中 reload 与 unload 的相互链接。

停用也可以通过复合而非规则直接链回激活。L-Unload 对目标视图不携带前提，因此无论纤维停用时目标视图变成什么，累加器都运行，纤维变为 Inactive，L-Begin 可立即从中启动新转移。

## 4.3.4. 失败（Failure）

迄今的每个规则都假设它运行的效应成功，而运行时不能。组件安装的效应延伸到跟踪它们的上下文之外，而它们到达的东西可能拒绝：已绑定的端口、不存在的文件、不应答的对端。失败的转移仍必须使纤维的效应被恢复而非搁浅。

令 $\Xi$ 为错误集并把定义 51 的效应迭代器精化，使迭代可以抛错而非产生三元组：

$$
\begin{array}{r l} \mathfrak {E} _ {\Gamma} ^ {\text {fail}} & := \mu \mathfrak {I}.   \Gamma \to \text {Either} (\Xi , \Gamma \times (\Gamma \to \Gamma) \times \text {Maybe} (\mathfrak {I})) \\ \mathfrak {E} _ {\Gamma} ^ {\text {fail*}} & := \mu \mathfrak {I}.   (e: \Gamma \to \text {Either} (\Xi , \Gamma \times (\Gamma \to \Gamma) \times \text {Maybe} (\mathfrak {I}))) \\ & \quad \times ((\gamma : \Gamma) \to (\text {let Right} (\delta , g, o) = e (\gamma) \text {in} g (\delta) \simeq \gamma)) \end{array}\tag{49}
$$

见证只约束 Right 情形，在模式不匹配处是空洞的，抛错没有要撤销的东西，而 Reloading 携带的 e 从此刻起在 $\mathfrak { E } _ { \Gamma } ^ { \mathrm { f a i l * } }$ 处读出。定义 52 的提升以抛错替代三元组传播过去，因此抛错的迭代器像普通迭代器一样可用于任何效应可用之处。本层增加一条规则并把定义 49 的第二个结果投入使用，O-Remove 无需加宽即可接纳它。L-Iter、L-Finish 和 L-Divert 的前提在其匹配的三元组周围以 Right 读出。抛错是迭代做的事，因此该规则是 Reloading 的一个出口。

$$
\frac {\theta_ {n} = \operatorname{Reloading} (i , g , \omega) \quad i (\gamma) = \operatorname{Left} (\xi)}{\gamma \longrightarrow \gamma [ \theta_ {n} \mapsto \operatorname{Unloading} (g , \omega , \xi) ]} \text { L - Raise }
$$

L-Raise 在记录之前恢复。纤维携带错误作为其结果路由进 Unloading，累积到失败迭代的累加器在那里被应用，纤维到达 Inactive(⊥)，未安装任何东西，其状态与中止的 L-Divert 所产生者仅在纤维携带的结果上不同。像每个其他停用一样路由失败，使每个结果只能经 L-Unlock 达到，这是定理 59 所依赖的唯一事实。L-Begin 以 Inactive(⊥) 为前提，因此生命周期不从错误结果重新进入；这是结果的实质，它不让其效应函数在其运行针对的状态中已显明不健全的纤维对未变的环境重试。失败的纤维也不阻碍任何东西：它 Inactive，因此不携带已提交视图、不能使 relied 成立。

失败记录在纤维上而非传播给其父，因此转移失败的组件让它的兄弟组件继续运行，这是插件宿主想要的行为，也是结果按纤维而非整个状态的性质的原因。

## 4.4. 元理论（Metatheory）

第 4.3 节提供十条规则：第 4.2 节的三条编排规则；激活的 L-Begin、L-Iter 和 L-Finish；激活提前结束的两种方式的 L-Divert 和 L-Raise；以及停用的 L-Leave 和 L-Unload。本节以全局形式读取这些规则的可组合性两个维度，一个纤维的保证无论其他纤维在其间做什么都成立，并加上只有整个系统才能被要求的东西：它总是达到其目标所要求的配置，且该配置是静态装配会产生的配置。下面的每个性质都是步骤序列的性质，因此我们对步骤编号并读取该编号状态中的字段。

两个约定把第 3.3.2 节带入本节。下面状态间的每个相等性都在定义 33 的观测等价 ≃ 之下读出，正如引理 38 读第 3.1 节的相等性，而效应函数所受的见证条件是定义 $^ { 3 7 }$ 给出的那个，按定义 51 对迭代器读出、在注册迭代处按下面的 ≈ 读出。

定义 53. 按 t 对步骤编号，使 $\gamma ^ { t }$ 是前 t 个步骤达到的状态，并写

$$
\operatorname{step} ^ {t} := r (n)\tag{50}
$$

为在 $\gamma ^ { t } \colon$ 处采取的步骤：它应用的规则 ρ（十条之一）以及它在该规则处应用的名字 $n \in \mathfrak { N }$ 。序列从 dom $\left( F ^ { 0 } \right) = \varnothing ,$ 的 $\gamma ^ { 0 }$ 开始，因此每个纤维都经 O-Insert 产生，无论是编排器的还是迭代采取的（定义 47）。$\gamma ^ { t }$ 的字段以上标携带索引，因此 $\theta _ { n } ^ { t } , \omega _ { n } ^ { t } , \sigma _ { n } ^ { t } , g _ { n } ^ { t }$ 和 $i _ { n } ^ { t }$ 是 n 在 $\gamma ^ { t } .$ 的生命周期状态、已提交视图、表、累加器和剩余迭代器，$F ^ { t }$ 和 $\sigma ^ { t }$ 是 $\gamma ^ { t }$ 本身的注册表和余效应上下文，即定义 45 在那里读出的 $F _ { \gamma }$ 和 $\sigma _ { \gamma }$ 。谓词以状态为参数、其余为下标，因此 $\mathrm{installed}_n^t$、$\mathrm{target}_n^t$、$\mathrm{reloaded}_n^t$ 和 quiet<sup>t</sup> 是定义 $^ { 4 6 , }$ 、定义 49 和定义 50 在 $\gamma ^ { t }$ 的谓词。n 的片段（episode）是 installe $\operatorname { l } _ { n } ^ { t }$ 成立的索引的最大区间 $[ b , u ]$ 。它在 $b ,$ 处打开，其中 $b >$ 0 且 $\neg \mathrm { i n s t a l l e d } _ { n } ^ { b - 1 }$ ，空 $F ^ { 0 }$ 开头不留纤维已安装；它在 installe $\mathbb { I } _ { n } ^ { u }$ 且非 installed $\mathsf { l } _ { n } ^ { \bar { u } + 1 }$ 的 t 处闭合，最终片段无需如此。

第 4.3 节的每个规则都以 $\gamma \longrightarrow \delta [ \cdots ] ,$ 的形状得出结论，其中前提从 $\gamma$ 计算 δ 并在它们不计算任何东西处把 δ 留为 $\gamma$ ，而方括号编辑注册表的命名字段。两半分别命名，且都是 Γ 上的映射。由作用于 n 的规则在 $\gamma ^ { t }$ 采取的步骤的状态映射是

$$
\Psi^ {t} := \left\{ \begin{array}{l l} \mathrm{pr} _ {1} \circ i & \text {at L - Iter, L - Finish, and a landing L - Divert} \\ g & \text {at L - Unload} \\ \mathrm{id} _ {\Gamma} & \text {at every other rule} \end{array} \right.\tag{51}
$$

其中 i 和 g 是 $\theta _ { n } ^ { t }$ 携带的迭代器和累加器，而编辑 edi $\mathrm { t } ^ { t } : \Gamma \to \Gamma$ 是把方括号作为函数读出的，为其命名的字段赋予前提在 $\gamma ^ { t }$ 计算的值。两者因此由 $\mathrm { s t e p } ^ { \bar { t } }$ 连同 $\gamma ^ { t }$ 固定并在每个状态有定义，这使定理 61 和引理 $7 1$ 能在远离 $\gamma ^ { t }$ 处求值它们。每步分解为

$$
\gamma^ {t + 1} = \mathrm{edit} ^ {t} \big (\Psi^ {t} \big (\gamma^ {t} \big) \big)\tag{52}
$$

例如在 L-Unload 处，edit<sup>t</sup> 是 $[ \theta _ { n }$ ↦ Inactive(⊥)]，在 O-Remove 处它是移除 $\setminus n ,$ 这就是后半是编辑而非赋值的原因。字段沿同一接缝划分：表 $\sigma _ { m } ,$ 没有 edit<sup>t</sup> 在创建 n 的 O-Insert 将其设为空后写入它们，以及控制字段 $\theta _ { m } , \tau _ { m } , \pi _ { m } , d _ { m } , p _ { m } , e _ { m }$ 连同 dom $\left( F _ { \gamma } \right)$ ，没有 $\Psi ^ { t }$ 除通过定义 47 的原语外写入它们。当两个状态在除控制字段外的一切上一致时写 γ ≈ γ′。

联系 ≈ 不是定义 33 的 ≃，两者互不细化，因为每个都遗忘另一个必须保留的东西。恢复精确性是关于效应的断言，因此 ≈ 精确比较表和环境状态，只遗忘注册表对哪个纤维安装它们的记录。规则读取控制字段以决定是否适用，因此 ≃ 必须保留它们，而本节把它读作定义 33 与注册表定义域及每个纤维每个控制字段一致的合取：

$$
\gamma \simeq \delta := \sigma_ {\gamma} \simeq \sigma_ {\delta} \wedge \operatorname{dom} \left(F _ {\gamma}\right) = \operatorname{dom} \left(F _ {\delta}\right) \wedge \forall n, c \in \{\theta , \tau , \pi , d, p, e \}. c (\gamma (n)) \simeq c (\delta (n)) (5 3)
$$

函数类型的字段，如 $e _ { n }$ 和 $\theta _ { n }$ 内部的 e ，按定义 36 比较映射，迭代器按定义 51 比较两个，任何其他类型的字段按相等性比较。下面的结果在这两个联系之下都成立，一个针对状态的一半，引理 55 一次性为全部十条规则确立 ≃ 一半。

表 1 是第 4.3 节的十条规则作为此类写入的解读。累加器、已提交视图和剩余迭代器是 $\theta _ { n } .$ 的构成部分，因此第三列也记录对它们的写入，第四列的 ℎ 命名该迭代产生的逆，L-Divert 中止该迭代处为 $\mathrm { i d } _ { \Gamma }$ 。由迭代器构建的 $\Psi ^ { t }$ 注册纤维处（定义 47），该注册在它抽取的名字携带 O-Insert 行的写入，而累加器退役纤维的 L-Unload 携带 O-Retire 行的写入。下面的每个情形分析都是表中的查找，而五个查找频繁到值得命名。

| 规则 | $\theta_{n}^{t}$ | $\theta_{n}^{t+1}$ | $\Psi^{t}$ | 控制字段 |
| --- | --- | --- | --- | --- |
| O-Insert | undefined | Inactive($\bot$) | id $_{\Gamma}$ | dom(F $_{\gamma}$ ) |
| O-Retire | unconstrained | unchanged | id $_{\Gamma}$ | $\tau_{n}$ |
| O-Remove | Inactive(−) | undefined | id $_{\Gamma}$ | dom(F $_{\gamma}$ ) |
| L-Begin | Inactive($\bot$) | Reloading(e $_{n}$ , id $_{\Gamma}$ , $\omega$) | id $_{\Gamma}$ | $\theta_{n}$ |
| L-Iter | Reloading(i, g, $\omega$) | Reloading(i′, g∘h, $\omega$) | pr $_{1}$ ∘i | $\theta_{n}$ |
| L-Finish | Reloading(i, g, $\omega$) | Active(g∘h, $\omega$) | pr $_{1}$ ∘i | $\theta_{n}$ |
| L-Divert | Reloading(i, g, $\omega$) | Unloading(g∘h, $\omega$, $\bot$) | id $_{\Gamma}$  或 pr $_{1}$ ∘i | $\theta_{n}$ |
| L-Raise | Reloading(i, g, $\omega$) | Unloading(g, $\omega$, ξ) | id $_{\Gamma}$ | $\theta_{n}$ |
| L-Leave | Active(g, $\omega$) | Unloading(g, $\omega$, $\bot$) | id $_{\Gamma}$ | $\theta_{n}$ |
| L-Unload | Unloading(g, $\omega$, ζ) | Inactive(ζ) | g | $\theta_{n}$ |


表 1 | 规则作为对它们作用的纤维 n 的写入，其中 step<sup>t</sup> 是在 n 处应用该规则。  
引理 54. 结合表 1 与定义 48 阅读，对每个步骤 t 和 $\gamma ^ { t } \colon$ 在场的所有纤维 n、m ：  
1. $\sigma _ { m } ^ { t + 1 } \neq \sigma _ { m } ^ { t }$ 仅在步骤 t 作用于 $m ,$ 且写入位于 $\Psi ^ { t } ;$ 内时成立；  
2. $\omega _ { n }$ 仅在 $\mathrm { s t e p } ^ { t } = \mathrm { L } \mathrm { - B e g i n } ( n )$ 处产生、仅在 $\mathrm { s t e p } ^ { t } =$ L-Unload(n) 处消失，因此 $\omega _ { n } ^ { t }$ 在 n 的片段内恒定；  
3. $\Psi ^ { t } = g _ { n } ^ { t }$ 仅在 step<sup>t</sup> = L-Unload(n) 处成立，且没有其他步骤把 $g _ { n }$ 应用于状态；  
4. ¬ installed<sup>t</sup> ∧ installe $\mathrm { l } _ { n } ^ { t + 1 } \Rightarrow \mathrm { s t e p } ^ { t } = \mathrm { L } \mathrm { - B e g i n } ( n )$ 且 installed<sup>t</sup> ∧ ¬ installed $^ { 1 + 1 } _ { n } \Rightarrow$ step<sup>t</sup> = L-Unload(n)；  
5. $\pi _ { n } , d _ { n } , p _ { n } ,$ 和 $e _ { n }$ 随 n 的条目产生且永不再写，$\tau _ { n }$ 单调，只在 ⊤ 处写且只由 O-Retire 写。

证明. 令步骤 t 在 n 处应用 ρ。由定义 53 它分解为 $\mathrm { e d i t } ^ { t } \circ \boldsymbol { \Psi } ^ { t } ,$ ，其中 edit<sup>t</sup> 只写表 1 第五列命名的字段，$\Psi ^ { t }$ 是 ${ \mathrm { i d } } _ { \Gamma } ,$ 、$n \mathrm { { 's } }$ 某次迭代的应用、或累加器 $g _ { n } ^ { t } ,$ ，后者是那些迭代产生的逆的复合。三者中的每一个都由定义 $^ { 4 8 , }$ 对 n 约束，因此 $\Psi ^ { t }$ 不写 $\gamma ^ { t }$ 在场纤维的任何字段（除 $\sigma _ { n } ,$ 连同注册添加的条目和其逆写的 θ）。两半因此划分写入，而每个条款是那个划分在一个字段处的解读。第二、三列的一个读法被使用两次：Inactive 是唯一不携带已提交视图的生命周期状态，L-Begin 是唯一离开它的规则，L-Unload 是唯一进入它的规则，而每个其他行把其前提的 δ 原样带入其结论。

(1) edit<sup>t</sup> 不写任何表（第五列不命名任何表），$\Psi ^ { t }$ 不写在场 m ≠ n 的 $\sigma _ { m }$。因此 $\sigma _ { m }$ 只能在 $m = n ,$ 处、且只在 $\Psi ^ { t }$ 内移动。

(2) $\omega _ { n }$ 是 $\theta _ { n } ,$ 的构成部分，只有 edit<sup>t</sup> 写它且只写步骤作用的纤维，因此由上面的读法，$\omega _ { n }$ 在 n 的 L-Begin 处产生、在 n 的 L-Unload 处消失。n 的片段是 installe $\mathsf { l } _ { n }$ 成立的区间，因此是 $\omega _ { n }$ 有定义的整个区间，两个规则都不落在其内部。

(3) 第四列中，累加器只在 L-Unload 处出现：其他规则取正向映射 pr ∘ e 或 ${ \mathrm { i d } } _ { \Gamma } ,$ 且没有 edit<sup>t</sup> 把映射应用于状态。

(4) installed 是 $\theta _ { n } \neq \mathsf { I n a c t i v e ( - ) }$ ，由上面的读法，L-Begin 和 L-Unload 是唯一其前提与结论在 $\theta _ { n }$ 是否 Inactive 上不同的规则。作用于 m $\neq$ n 的步骤不写 $\theta _ { n } ,$ 而注册添加的条目位于 $\gamma ^ { t } .$ 缺席的名字。

(5) 第五列没有行命名 $\pi , d , p , \mathrm { o r } e ;$ 那些随 O-Insert 添加的条目产生，其结论写它们，注册采取的 O-Insert 也一样。只有 O-Retire 写 $\mathrm { ~ a ~ } \tau ,$ 在 $\top .$ 处，无论由编排器采取还是作为注册的逆（定义 $4 7 ) ; 0 \cdot$ -Insert 在缺席名字处设 $\tau = \bot$ ，因此没有步骤把 $\mathtt { a } \tau$ 返回 $\pm . \square$

三个进一步的查找说明规则看不到什么。第一个是它们只通过上面的观测读取状态，因此整个演算下降到 $\Gamma / \simeq$

引理 55. （≃-不变性。）令 $\gamma \simeq \gamma ^ { \prime }$ 按上面读法。则第 4.3 节的规则在 $\gamma$ 作用于 n 处适用当且仅当它在 $\gamma ^ { \prime }$ 作用于 $n ,$ 处适用，且两次应用达到的状态又由 $\simeq$ 相关

证明. 第 4.3 节的每个前提都属于四种之一，每个读取联系保留的构成部分。把 $\theta _ { n }$ 或 $\tau _ { n }$ 与模式匹配的前提，以及 O-Remove 的前提 ∀m. $\pi _ { m } \neq n$ ，读取控制字段。O-Insert 的前提 $( d , p , e ) \in \mathfrak { C } _ { \Gamma }$ 和 ∀m. $p \cap p _ { m } = \mathcal { O }$ 读取 $d , p ,$ 和 $e . \mathrm { A }$ 提及 ta $\mathrm { \ ; g e t } _ { n }$ 或 $\mathrm { r e l i e d } _ { n }$ 的前提读取 $\tau _ { n } ,$ 、$\theta _ { m }$ 内部的已提交视图和 dom $\left( \sigma _ { \gamma } \right)$ ，后者由定义 45 从 $\theta _ { m }$ 和 dom $( \sigma _ { m } )$ 计算，而定义 33 只在定义域一致时关联两个余效应上下文。剩余前提读取 dom $\left( F _ { \gamma } \right)$ 。没有一个以 ${ \widetilde { \overline { { k } } } } ^ { \prime }$ 之外的方式读取值 $\sigma _ { \gamma } ( k )$ ，因此没有前提分离两个 ≃-相关状态。

对结论，由定义 53 $\gamma ^ { t + 1 } = \mathrm { e d i t } ^ { t } \big ( \Psi ^ { t } \big ( \gamma ^ { t } \big ) \big )$ ) 。edit<sup>t</sup> 赋予的值是它匹配的前提的构成部分，由上面一段和定义 51 在两个状态处相关，定义 51 关联迭代器在 ≃-相关状态处产生的三元组。而 $\Psi ^ { t }$ 尊重 $\simeq$ 它是 $\mathrm { i d } _ { \Gamma }$ 、或 $e _ { n } ,$ 的迭代，定义 51 要求其尊重 $\simeq ,$ 或 $\theta _ { n } ,$ 内部的累加器，即每个都按同一定义尊重 ≃ 的逆的复合。 □

状态携带的名字由其中两个观测读取，dom $\left( F _ { \gamma } \right)$ 和控制字段的索引，而抽取名字的规则抽取任何未使用的名字（定义 $4 7 )$ 。因此把下面的结果读作 ≃ 之下也需要把它们读作重命名之下，这是第 4.1 节纪律的兑现。

引理 56. （等变性。）令 $\chi : \mathfrak { N } \to \mathfrak { N }$ 是双射并令 $\chi \cdot \gamma$ 是携带注册表 $F _ { \gamma } \circ \chi ^ { - 1 }$ 的状态，$\pi _ { m }$ 或 $\omega _ { m }$ 中出现的每个名字都被其像替换。则 $\chi$ $\gamma$ 是状态，在 $\gamma$ 良构处良构，且 ste $\mathrm { p } ^ { t } = r ( n )$ 把 $\gamma ^ { t }$ 带到 $\gamma ^ { t + 1 }$ 当且仅当 $r ( \chi ( n ) )$ ) 把 $\chi \cdot \gamma ^ { t }$ 带到 $\chi \cdot \gamma ^ { t + 1 }$

证明. 前提只通过把它与另一名字比较来读取名字，无论是直接的（O-Insert 的新鲜性 $n \not \in$ dom $\left( F _ { \gamma } \right)$ 和 O-Remove 的 $\forall m . \ \pi _ { m } \neq n$ ），还是通过名字表（$\mathrm{target}_n$ 和 $\mathrm { r e l i e d } _ { n }$ 读取 $\pi _ { m }$ 和 $\omega _ { m } . \mathrm { A }$ 双射保持每个这样的比较。规则只写 O-Insert 设置的 $\pi$ 和 L-Begin 设置的 ω，两者都取自其前提所读，因此写入与 $\chi ;$ 交换；效应函数完全不写名字，只通过定义 $^ { 4 7 , }$ 的原语抽取一个，定义 48 把其约束到该原语添加的条目。良构性（定义 58）是四个把名字与名字比较的条件。 □

因此序列及其重命名以相同顺序采取相同规则并达到仅差 $\chi$ 的状态。除注册抽取的名字外一致的两个序列随之被等同，而下面的结果在该等同它们的重命名之下读出。

第二个查找是剥除名字外一切只剩名字的条目对规则不可见，这使定义 $4 7$ 能在其恢复的状态没有该纤维处退役一个纤维，使引理 72 移除被删除片段做出的注册。

引理 57. （残余条目。）当 $\tau _ { n } = \top , \theta _ { n } = \mathsf { I n a c t i v e ( \bot ) } , \sigma _ { n } = \emptyset$ 且没有 m 有 $\pi _ { m } = n ;$ 时称 n 在 γ 处是残余的；残余条目满足 $\gamma \approx \gamma \setminus n$ 。若 n 在 $\gamma$ 处残余，则对每个规则和每个 m ≠ n：

1. 在 $\gamma$ 作用于 n 的规则在 $\gamma \setminus$ n 作用于 $m ,$ 处适用，且两者达到的状态只在 n 的条目处不同，后者保持残余；

2. 反之在 $\gamma \setminus n$ 作用于 n 的规则在 $\gamma ,$ 处适用，除非它是抽取名字 n 或主张 $p _ { n }$ 的键的 O-Insert

证明. 残余 n 不贡献作用于 m $\neq n$ 的规则前提读取的任何观测。它不 Active，因此 $\sigma _ { n }$ 不进任何 $\sigma _ { \gamma }$ ，n 不提供任何键，使 $\gamma \models d _ { m }$ 和 $\mathrm { t a r g e t } _ { m }$ 不动；installed $\mathsf { l } _ { n }$ 失败，因此 n 不贡献 relied $_ { m } ;$ 的析取；没有 $\pi _ { m ^ { \prime } }$ 命名 $n ,$ 因此 n 的 O-Remove 的前提 $\forall m ^ { \prime } . \pi _ { m ^ { \prime } } \neq$ n 不动；而 $\theta _ { n } , \tau _ { n } ,$ 和 $\pi _ { n }$ 由作用于 n 的规则读取。条款 (2) 例外的两个前提是移除所放松的两个，缺席名字是新名、缺席提供满足每个其他提供。由引理 54，作用于 $m \neq n$ 的规则不写 $n$ 的字段，因此条目存活，且步骤的状态映射由定义 48 对 n 约束，因此它使 $\sigma _ { n }$ 为空。 □

简化生命周期状态以及匹配它们的规则得到一个子演算，且并非每个结果都在简化下存活。放弃第 4.3.1 节是重要情形，即第 4.3 节开头从元理论侧读出的划分：其守卫确立定义 58 的条款 (3) 和 (4)，而定理 63 依赖守卫创造的区间，因此没有它这三者失败。其他三个小节添加的内容可以在不扰动下面结果的情况下简化掉，每个都只是向定义 49 固定的同一状态空间添加规则。

## 4.4.1. 保真（Preservation）

定义 45 固定注册表的形状，在下面的结果能向它添加内容之前，规则必须对照它检查。本小节识别规则保持的不变量，其第一条款就是那个形状，其余是那些结果所假设的。

定义 58. 注册表 $F _ { \gamma }$ 是良构的，当对所有 $m , n \in \mathop { \mathrm { d o m } } \bigl ( F _ { \gamma } \bigr )$ 和所有 $k \in K$

1. $\pi _ { n } \in$ dom(F<sub>γ</sub>) ∪ {root}；

2. m $\neq n \Rightarrow p _ { m } \cap p _ { n } = \emptyset ;$

3. ins $\mathrm { t a l l e d } _ { n } ( \gamma ) \Rightarrow \omega _ { n }$ 在 $d _ { n }$ 上全定义且取值在 dom $\left( F _ { \gamma } \right)$ ；

4. installed<sub>n</sub>(γ) ∧ k ∈ d<sub>n</sub> ∧ ω<sub>n</sub>(k) = m ⇒ installed<sub>m</sub>(γ)。

条款 (1) 是定义 45 的树一次一条边读出，保持父指针落在注册表内。该定义还要求的非环性不需要条款，因为指针命名的纤维在命名它的纤维注册之前注册。

定理 59. （保真。）若 $F ^ { t }$ 良构则 $F ^ { t + 1 }$ 良构，无论步骤 t 应用哪个规则。每个条款在 $\gamma ^ { t + 1 }$ 处由 $\gamma ^ { t }$ 的全部四个确立。

证明. 令步骤 t 作用于 n。

(1) 由表 1 只有 O-Insert 和 O-Remove 写 π 或 dom $\left( F _ { \gamma } \right)$ 。O-Insert 以 $\pi _ { n } \in \mathrm { d o m } ( F ^ { t } ) ~ |$ ∪ {root} 为前提，即它添加的纤维的条款，并在扩大 dom $\left( F _ { \gamma } \right)$ 的同时让每个其他 $\pi$ 独处。O-Remove 以 ∀m. $\pi _ { m } \neq n ,$ 为前提，因此没有存活的 $\pi _ { m }$ 命名它带走的纤维。

(2) O-Insert 的最后一个前提是 ∀m. $p _ { n } \cap p _ { m } = \emptyset$ ，即它添加的纤维的条款，且由表 1 没有其他规则写 π 或扩大 dom $\left( F _ { \gamma } \right)$ 。下面使用两个推论：dom $( \sigma _ { m } ) \subseteq p _ { m }$ 由定义 $^ { 4 3 , }$ 因此不同表不相交且 $\sigma _ { \gamma }$ 是函数；$k \in p _ { m } \cap$ $p _ { m ^ { \prime } }$ 迫使 $m = m ^ { \prime }$ ，因此 k 至多有一个可能的提供者。

(3) 由引理 $5 4 ( 2 )$ 唯一写 $\omega _ { n }$ 的规则是 L-Begin，其前提 $\omega = \mathrm { t a r g e t } _ { n } ^ { t } \neq \perp$ 使它全定义在 $d _ { n }$ 上且取值在 dom $\left( F ^ { t } \right)$ ，target 命名提供者。由表 1 唯一缩小 dom $\left( F _ { \gamma } \right)$ 的规则是 O-Remove，其前提 $\theta _ { n } ^ { t } = \mathsf { I n a c t i v e } ( - )$ 给出 $\lnot \mathrm { i n s t a l l e d } _ { n } ^ { t }$ ，当由 $\gamma ^ { t }$ 的条款 (4) 没有 n 在 installe $\mathrm { l } _ { m } ^ { t } ;$ 时对 $k \in d _ { m }$ 有 $\omega _ { m } ^ { t } ( k ) = n$ ；且 n 本身不携带 ω。

(4) 由引理 $5 4 ( 2 )$ 和 (4)，条款只能在 $\gamma ^ { t + 1 }$ 处失败，若某个已安装者倒下、某个 ω 被写、或某 π 命名的纤维离开 dom $\left( F _ { \gamma } \right)$ 。最后者是 O-Remove，其被移除纤维不安装，因此由 $\boldsymbol { \gamma } ^ { t }$ 的条款 (4) 不被已安装 $m _ { \cdot }$ 的任何 $\omega _ { m } ^ { t }$ 命名。第一个是 $n ,$ 的 L-Unload，其前提 $\mod _ { n } ^ { t }$ 读

$$
\forall m \neq n, k \in d _ {m}. \mathrm{installed} _ {m} ^ {t} \Rightarrow \omega_ {m} ^ {t} (k) \neq n
$$

且它不写 m $\neq n$ 的任何 $\omega _ { m }$ 、留下 $\neg { \mathrm { i n s t a l l e d } } _ { n } ^ { t + 1 }$ ，因此条款也对 n 成立。第二个是 $n ,$ 的 L-Begin，写 $\mathrm { t a r g e t } _ { n } ^ { t } ,$ 其值是 $d _ { n }$ 各键的提供者、因此在 $\gamma ^ { t }$ 处 Active；该步骤不改变其他 ${ \mathrm { f i b e r } } ^ { \prime } \mathbf { s } \theta ,$ 因此它们在 $\gamma ^ { t + 1 }$ 处也已安装。 □

L-Unload 上的守卫是承载条款 (3) 和 (4) 的东西。O-Remove 的前提 ∀m. $\pi _ { m } \neq$ n 只谈父指针；使已提交视图不命名被移除纤维的是守卫，它在数步之前因不同理由施加。因为失败也经 Unloading 路由，该论证不必为错误结果重复。基础演算不享有的两件事随之而来。O-Remove 释放的名字可被 O-Insert 重新签发，因为没有过期的已提交视图能命名它；纤维一旦 Inactive 即可移除，无需单独检查是否有人依赖它。

## 4.4.2. 时间可组合性（Temporal Composability）

局部时间可组合性用一个累加器恢复一个效应序列（第 3.1.3 节）。注册表为每个纤维持有一个累加器，而纤维交错：在 n 把逆复合到 $g _ { n }$ 的时刻与 $g _ { n }$ 运行的时刻之间，其他纤维已移动状态。$g _ { n }$ 是否仍在那里撤销它被构造来撤销的东西是全局形式所断言的，而它所依赖的条件是介入步骤与 $g _ { n }$ 交换。

定义 60. 对 $i \in { \mathfrak { E } } _ { \Gamma } ^ { \mathrm { i t e r * } }$ 令 reach(i) 是包含 i 并在续延下封闭的最小迭代器集，并把定义 17 的变换幺半群 M 在迭代器处读出，以 reach(i) 中每个迭代器的正向映射和产生的逆作为其生成元：

$$
\begin{array}{c} \operatorname{reach} (i) := \bigcap \{S \mid i \in S \land \forall i ^ {\prime} \in S, \gamma \in \Gamma .   i ^ {\prime} (\gamma) = (-, -, \operatorname{Just} (i ^ {\prime \prime})) \Rightarrow i ^ {\prime \prime} \in S \} \\ \mathfrak {M} (i) := \langle \{\operatorname{pr} _ {1} \circ i ^ {\prime} \mid i ^ {\prime} \in \operatorname{reach} (i) \} \cup \{\operatorname{pr} _ {2} (i ^ {\prime} (\gamma)) \mid i ^ {\prime} \in \operatorname{reach} (i), \gamma \in \Gamma \} \rangle \end{array}\tag{54}
$$

在第 4.3.4 节适用处把 Right 读作三元组周围，并写 len(i) 为续延排序的链 $C \subseteq \mathrm { r e a c h } ( i )$ 上 $| C |$ 的上确界。两个迭代器 $i , j$ 独立，当它们按定义 19 的意义独立，这些变换幺半群读出，迭代的产出是其逆连同其续延：

$$
\begin{array}{r l} \forall f \in \mathfrak {M} (i), g \in \mathfrak {M} (j). & f \circ g \simeq g \circ f \\ \forall i ^ {\prime} \in \mathrm{reach} (i), g \in \mathfrak {M} (j), \gamma \in \Gamma . & \mathrm{pr} _ {2, 3} (i ^ {\prime} (g (\gamma))) \simeq \mathrm{pr} _ {2, 3} (i ^ {\prime} (\gamma)) \end{array}\tag{55}
$$

在 $j$ 中对称，映射上的 ≃ 按定义 36 读、续延上的按定义 51 读、注册迭代（定义 47）上的按它命名的组件的一致读。迭代器族 $\left( i _ { l } \right) _ { l \in L }$ 两两独立，当对每个 ${ \mathit { l } } \neq { \mathit { l } } ^ { \prime }$ 的 $i _ { l }$ 和 $i _ { l ^ { \prime } }$ 独立，而步骤序列两两独立，当 $\left( e _ { n } \right) _ { n \in N }$ 如此，其中 N 是序列曾持有的名字集，编排器插入的每个纤维和迭代注册的每个纤维各一。

这个意义上的独立性正是迹理论取其原始的东西：交换动作在序列上生成等价，在其下重排两个相邻独立动作保持端点 [44]，而引理 71 对这些规则就是那个重排。族而非集是保持一个组件两个名字在作用域内的东西：条件随后要求该组件的效应函数与自身独立，即要求 M(e) 交换。第一条件定理 61 使用，第二条件定理 73 还需要：重排两个纤维的步骤在另一纤维移动的状态处求值迭代器，而交换映射本身并不说明迭代器在那里产生相同的逆和相同的续延。检查第一条件只需迭代本身，因为引理 18(1) 把交换性从生成元带到它们生成的幺半群。

在这些条件下，定理 7 的单累加器不变量在交错下存活，形式是给时间可组合性以内容的那个：运行逆撤出纤维的贡献而别无其他。

定理 61. （恢复精确性。）令步骤序列两两独立，令 n 的片段在 b 处打开、$u \geq b$ 位于其中，并令 $t _ { 1 } < \dots < t _ { l }$ 是 $[ b , u )$ 中作用纤维非 n 的索引。则

$$
g _ {n} ^ {u} (\gamma^ {u}) \approx \big (\Psi^ {t _ {l}} \circ \dots \circ \Psi^ {t _ {1}} \big) \big (\gamma^ {b} \big)\tag{56}
$$

即，在 $\gamma ^ { u }$ 处应用 n 的累加器产生，在控制字段之下，那些相同步骤从 $\gamma ^ { b }$ 产生的状态。把右侧读作 n 从未开始会达到的状态还额外假设没有 n 注册的纤维在 $[ b , u )$ 采取步骤，因为 n 注册的纤维是本来不会在那里采取它的纤维。

证明. 对 $u ,$ 在片段内满足 t + 1 的索引 t 上归纳。在 t = b 处，$b - 1$ 的步骤是 L-Begin（片段按定义 53 打开），因此由表 1 $g _ { n } ^ { b } = \mathrm { i d } _ { \Gamma }$ ，索引集为空，断言是 $\bar { \gamma } ^ { b } \approx \gamma ^ { b }$ 。每步使用两个事实。由于 edit<sup>t</sup> 只写控制字段，

$$
\gamma^ {t + 1} \approx \Psi^ {t} (\gamma^ {t})
$$

且由于 ${ \mathfrak { M } } ( e _ { n } )$ 中每个映射除注册添加的控制字段外不写任何控制字段（由定义 48 连同定义 47），每个这样的映射把 ≈-相等状态带到 ≈-相等状态。

令步骤 t 作用于 n。由于片段在 t 和 $u + 1$ 打开，引理 $5 4 ( 4 )$ 排除 $n ,$ 的 L-Begin 和 L-Unload，而 O-Insert 和 O-Remove 读取 installed<sup>t</sup> 所否定的 $\theta _ { n }$ ，留下两种情形。规则是 L-Iter、L-Finish 或落地 L-Divert 时，表 1 给出 $\Psi ^ { u } = \mathrm { p r } _ { 1 } \circ i _ { n } ^ { u }$ 和 $g _ { n } ^ { u + 1 } = g _ { n } ^ { u }$ ∘ ℎ，其中 ℎ 是该迭代产生的逆。定义 51 的见证条件读 $h ( \Psi ^ { u } ( \gamma ^ { u } ) ) = \gamma ^ { u }$ ，在迭代注册纤维处读到 ≈（引理 57），而 $g _ { n } ^ { u }$ 由上式携带 ≈，因此

$$
g _ {n} ^ {u + 1} (\gamma^ {u + 1}) \approx (g _ {n} ^ {u} \circ h) (\Psi^ {u} (\gamma^ {u})) = g _ {n} ^ {u} (\gamma^ {u})
$$

规则是 L-Leave、L-Raise、中止 L-Divert 或 $n ,$ 的 O-Retire 时，表 1 给出 $\Psi ^ { u } = \mathrm { i d } _ { \Gamma }$ 和 $g _ { n } ^ { u + 1 } = g _ { n } ^ { u } ,$ 因此同一等式以 $h = \mathrm { i d } _ { \Gamma }$ 成立。两种情形下归纳假设以不变的索引集传递，这就是定理 7 一次一步的计算。

令步骤 t 作用于 n ≠ $_ n$ 。则表 1 给出 $g _ { n } ^ { u + 1 } = g _ { n } ^ { u }$ ，且 $\Psi ^ { u } \in \mathfrak { M } ( e _ { m } )$ ，或规则是编排规则时 $\Psi ^ { u } = \mathrm { i d } _ { \mathrm { I } }$ ，因此独立性给出

$$
g _ {n} ^ {u} (\gamma^ {u + 1}) \approx g _ {n} ^ {u} (\Psi^ {u} (\gamma^ {u})) = \Psi^ {u} (g _ {n} ^ {u} (\gamma^ {u}))
$$

即带追加 $\Psi ^ { u }$ 的归纳假设。

推论 62. （终点恢复。）令步骤序列两两独立并令 n 的片段在 b 处打开、在 $u ,$ 处闭合，无论 n 到达什么结果。则，$t _ { 1 } < \cdots < t _ { l }$ 如定理 61，

$$
\gamma^ {u + 1} \approx \left(\Psi^ {t _ {l}} \circ \dots \circ \Psi^ {t _ {1}}\right) \left(\gamma^ {b}\right)\tag{57}
$$

O-Remove 移除的纤维也不留下任何东西，其前提只接纳 $\theta _ { n } =$ Inactive(−)。

证明. 由引理 54(4) 步骤 t 是 $n ,$ 的 L-Unload，其 $\Psi ^ { u }$ 由引理 $5 4 ( 3 )$ 是 $g _ { n } ^ { u } , { \bf s o \gamma } \gamma ^ { u + 1 }$ ≈ $g _ { n } ^ { u } ( \gamma ^ { u } )$ 而定理 61 适用。声明和 ≈ 都不提 $\zeta ,$ 由表 1 它是 L-Divert 和 L-Raise 导致的状态不同的唯一字段。 □

上面的结果假设组件两两独立，而第 3.3.2 节结清它：在组件执行的每个效应是一个键的操作且每个键交换处，任何两个由这些操作构建的效应函数独立（定理 42）。把该结果从效应函数带到迭代器无需新东西，余效应中介的效应函数（定义 41）已经按阶段产生的结果选择其后续，这正是迭代器在其续延中携带的东西。第 3.2 节的余效应操作是完全无需假设的情形：组件在那里贡献的映射是 set 操作和相应限制的复合，两个这样的映射在触碰不相交键时交换，而定义 58 的条款 (2) 使不同纤维的提供不相交。

## 4.4.3. 空间可组合性（Spatial Composability）

局部空间可组合性把组件保持在其自身规范上，只在依赖被提供处激活它，并依据规范分类每次上下文变化（第 3.2.2 节）。全局形式加入量化其他纤维的东西：提供者只在每个把某键解析到它的依赖方已停用后才撤出该绑定，且转移据以安装其效应的解析不会在其下移动。余效应侧的两个性质交付两者，且它们一起证明，因为它们是一个不变量的两半，即引理 54(2) 确立的 $\omega _ { n }$ 在片段上的固定性。排序定理是该固定性在 n 是 Active 然后 Unloading 的片段部分上买来的，相干定理是它在 n 安装其效应的部分上买来的。

定理 63. （排序。）纤维只在依赖被提供处开始转移：

$$
\mathrm{step} ^ {t} = \mathrm{L-Begin} (m) \Rightarrow \gamma^ {t} \vDash d _ {m}\tag{58}
$$

再令 $[ b ^ { \prime } , u ^ { \prime } ]$ 是 n 的片段，对某个 m $\neq$ n 和 $k \in d _ { m }$ 有 $\omega _ { m } ^ { b ^ { \prime } } ( k ) = n ,$ 令 $[ b , u ]$ 是包含 $b ^ { \prime } ,$ 的 n 的片段，并令 t 遍历 $[ b ^ { \prime } , u ^ { \prime } ]$ 。则

1. $\omega _ { m } ^ { t } ( k ) = n ;$

2. $b < b ^ { \prime } .$ ，且 $[ b , u ]$ 闭合则 $u ^ { \prime } < u ;$

3. $k \in \mathrm { d o m } ( \sigma _ { n } ^ { t } )$ 且 $\sigma _ { n } ^ { t } ( k ) = \sigma _ { n } ^ { b ^ { \prime } } ( k )$

证明. 第一个断言是 L-Begin 的前提 t $\mathrm { a r g e t } _ { m } ^ { t } \neq \perp$ ，由定义 46 它给出 $\gamma ^ { t }$ ⊧ $d _ { m }$

(1) 是引理 54(2)。

对 (2)，$b ^ { \prime } - 1$ 处的 L-Begin 写 $\omega _ { m } ^ { b ^ { \prime } } = \mathrm { t a r g e t } _ { m } ^ { b ^ { \prime } - 1 }$ ，其值是提供者，因此 $\theta _ { n } ^ { b ^ { \prime } } =$ $\mathsf { A c t i v e ( - , - ) } ;$ $b - 1$ 处的 L-Begin 留下 $\theta _ { n } ^ { b } = { \mathsf { R e l o a d i n g } } ( - , - , - )$ ，因此 $b \neq b ^ { \prime }$ 从而 $b < b ^ { \prime }$ 两者片段都按定义 53 打开。令 $[ b , u ]$ 闭合并假设 $u \leq u ^ { \prime }$ 。则 $u \in [ b ^ { \prime } , u ^ { \prime } ] .$ 因此 installed $\mathbb { I } _ { m } ^ { u }$ 且由 $( 1 ) , \omega _ { m } ^ { u } ( k ) = n ;$ 那是 relied<sup>n</sup>，n 处的 L-Unload 否认它。因此 $u ^ { \prime } < u$

对 (3)，n 在 $\gamma ^ { b ^ { \prime } }$ 处是 k 的提供者，因此 $k \in \mathrm { d o m } \bigl ( \sigma _ { n } ^ { b ^ { \prime } } \bigr )$ 。$[ b ^ { \prime } , u ^ { \prime } ]$ 内没有 n 的 L-Unload：$[ b , u ]$ 闭合处它落在 $u > u ^ { \prime }$ （由 (2)），不闭合处引理 54(4) 使 n 完全没有 L-Unload。由于 $\theta _ { n } ^ { b ^ { \prime } } = \mathsf { A c t i v e } ( - , - )$ ，表 1 因此使 L-Leave 成为 n 在 $[ b ^ { \prime } , u ^ { \prime } ]$ 内能被作用上的唯一规则，其 $\Psi ^ { t }$ 是 $\operatorname { i d } _ { \Gamma } ;$ 由引理 $5 4 ( 1 ) ~ \sigma _ { n }$ 在那里恒定。 □

否则跨越步骤的转移会安装针对其下已改变的解析计算的效应，而两个前提防止它。L-Iter 和 L-Finish 携带 $\mathrm { t a r g e t } _ { n } ( \gamma ) = \omega ,$ ，因此转移只在其已提交视图仍是其目标视图时进行，L-Divert 携带其否定，因此目标视图的任何改变都把纤维带出转移。L-Raise 完全不受目标视图条件限制，抛错是迭代做的事而非环境要求的，且它无论如何退出转移。变化的两个方向不加区分：依赖消失的组件和依赖被替换的组件走同一条路，因为已变为 ⊥ 的目标视图和已变为其他纤维的目标视图同样不等于 ω。

惯性是使它不成为关于每步的保证的东西。目标视图转向时已在飞行的迭代无论如何落地（由 L-Divert），而那个落地安装针对不再成立的解析计算的效应。规则因此交付一个析取，第二支使第一支安全。

定理 64. （解析相干性。）令 n 的片段 $[ b , u ]$ 在 b 处以 $\omega _ { n } ^ { b } = \omega$ 打开。则 $\theta _ { n }$ 在片段的初始区间 $[ \bar { b } , r ]$ 上是 Reloading $( - , - , - )$ ，且转移的每次迭代都针对唯一解析 ω 运行：

$$
\forall t \in [ b, r ]. \mathrm{step} ^ {t} \in \{\mathrm{L-Iter} (n), \mathrm{L-Finish} (n) \} \Rightarrow \mathrm{target} _ {n} ^ {t} = \omega\tag{59}
$$

纤维离开该区间（$r < u ,$ ）处，恰好下列之一成立：

1. ste $\mathbf { \omega } ) ^ { r } = \mathrm { L } { \mathrm { - F i n i s h } } ( n )$ 且 $\theta _ { n } ^ { r + 1 } = \mathsf { A c t i v e } ( - , \omega ) ;$ ；

2. st $\mathsf { s p } ^ { r } \in \{ \mathrm { L } \mathrm { - D i v e r t } ( n ) , \mathrm { L } \mathrm { - R a i s e } ( n ) \}$ ，且片段在某个 $u > r$ 处闭合，$\gamma ^ { u + 1 }$ ≈ $\left( \Psi ^ { t _ { l } } \circ \cdots \circ \Psi ^ { t _ { 1 } } \right) \left( \gamma ^ { b } \right)$ 如推论 62。

证明. $b - 1$ 处的 L-Begin 写 Reloading，由表 1 它是进入该生命周期状态的唯一规则；其前提 $\theta _ { n } = \mathsf { I n a c t i v e } ( \bot )$ 和引理 $5 4 ( 4 )$ 把它的任何第二次应用放在片段外。因此 Reloading 占据 $[ \bar { b , r } ] \mathrm { o f } [ \bar { b } , u ]$ 的初始区间且不被重新进入。

第一个断言随后是表 1 给 L-Iter 和 L-Finish 的前提 targe $\mathfrak { t } _ { n } ( \gamma ) = \omega ^ { \prime }$ ，连同 $\omega ^ { \prime } = \omega$ （由引理 $5 4 ( 2 )$ ）

对二分，step<sup>t</sup> 是其前提有 $\theta _ { n } = { \mathsf { R e l o a d i n g } } ( - , - , - )$ 而结论没有的规则，表 1 提供 L-Finish、L-Divert 和 L-Raise；前者落在 $\mathsf { A c t i v e } ( - , \omega )$ 而另两个落在 $\mathsf { U n l o a d i n g ( - , } \omega , - \mathsf { ) }$ ，从那里引理 54(4) 使 L-Unload 成为唯一出口而推论 62 提供等式。落地 L-Divert 贡献的迭代是 $n \mathrm { { 's } }$ 自己的，因此在累加器撤出的映射之中。而 $r = u ,$ 处，序列以转移仍在飞行结束，只断言第一个断言。 □

## 4.4.4. 进展性（Progress）

把提供者撤出推迟到其依赖方离开的守卫，只有在它最终释放时交付定理 63。注册表纤维上的一个联系承载该论证。

定义 65. 注册表名字上的优先关系是

$$
n \prec m := p _ {n} \cap d _ {m} \neq \emptyset\tag{60}
$$

因此 n 可能提供 m 声明的键。它只读 π 和 d ，由引理 $5 4 ( 5 )$ 两者随纤维条目产生且永不再写。

定理 66 和定理 73 在 ≺ 无环的假设下确立，这是一个假设而非定义交付的东西，$n \prec n$ 对声明自己提供键的组件成立。≺ 排序的是两个纤维的激活而非其寿命：$n \prec m$ 说 n 必须先在 m 之前变为 Active，而提供者比其消费者长寿是定理 63(2)，一个关于受守卫演算的定理。

纤维的目标视图既应答创建它的纤维也应答其提供者。创建者写的是 $\tau _ { n } ,$ 通过定义 $^ { 4 7 , }$ 的原语，而 τ 由引理 54(5) 单调。创建者因此最多在其子组件的整个存在期间把子的目标视图转向一次。

进展性是某个规则适用的断言，因此它针对宿主必须提供的规则表述：L-Begin、L-Leave、L-Unload、落地规则 L-Iter、L-Finish 和 L-Raise，以及 L-Divert。它无处诉诸 L-Divert 的中止备选，因此受第 4.3.3 节惯性约束的宿主也被覆盖。

定理 66. （进展性。）假设 ≺ 无环，对每个 $n ,$ 有 len $( e _ { n } ) \leq K$ ，且定义 60 的名字集 N 有限；并令每个步骤应用生命周期规则。写 $S ( n )$ 为作用于 n 的步骤数

$$
V (n) := \left| \left\{t: \mathrm{target} _ {n} ^ {t} \neq \mathrm{target} _ {n} ^ {t + 1} \right\} \right|\tag{61}
$$

为其目标视图转向的次数。则

1. （无死锁。）¬ quiet<sup>t</sup> 蕴含某个生命周期规则在 $\gamma ^ { t } ;$ 处适用；

2. （终止。）$S ( n ) \leq ( K + 4 ) ( V ( n ) + 1 )$ ，且 $V ( n )$ 与 $\textstyle \sum _ { n } S ( n )$ 都有限。因此每个最大的生命周期步骤序列都以静止状态结束。

证明. 无死锁。令 $\neg \mathrm { q u i e t } ^ { t } ,$ 则某个纤维 n 不满足定义 49 的静止性的任一条款。对照表 1 读它可能处于的四种：

$\theta _ { n } ^ { t } = \mathsf { I n a c t i v e } ( \bot )$ 且 targe $^ { . t } _ { n } \neq \perp \colon \mathrm { L } \cdot \mathrm { B } { \sf t }$ egin 适用；

$\theta _ { n } ^ { t } = \mathsf { R e l o a d i n g } ( - , - , \omega _ { n } )$ 且 targe $\mathbf { t } _ { n } ^ { t } = { \boldsymbol { \omega } } _ { n }$ ：$i _ { n } ^ { t } ( \gamma ^ { t } )$ 的值所选择的 L-Iter、L-Finish、L-Raise 中任意一个适用；

$\theta _ { n } ^ { t } = \mathsf { R e l o a d i n g } ( - , - , \omega _ { n } )$ 且 targe $\mathrm { t } _ { n } ^ { t } \neq \omega _ { n } \mathrm { : }$ $i _ { n } ^ { t } ( \gamma ^ { t } )$ 抛错则 L-Raise 适用，否则 L-Divert 适用，落地该迭代而非中止它；

$\theta _ { n } ^ { t } = \mathsf { A c t i v e } ( - , \omega _ { n } )$ 且 targ $\operatorname { e t } _ { n } ^ { t } \neq \omega _ { n } \colon$ ：L-Leave 适用。

令没有纤维属于任何这类，留下某个 $\theta _ { m _ { 0 } } ^ { t } = \mathsf { U n l o a d i n g } ( - , - , - )$ 的 $m _ { 0 }$ 。如下构造 $m _ { 0 } , m _ { 1 } , \ldots$ ：给定 Unloading 中的 $m _ { j }$ ，要么 $\mathrm { \neg ~ r e l i e d } _ { m _ { j } } ^ { t } ,$ 此时 L-Unload 适用于 $m _ { j }$ 且构造停止，要么存在 $m _ { j + 1 } \neq m _ { j }$ 和 $k _ { j }$ 使 $\mathrm { i n s t a l l e d } _ { m _ { j + 1 } } ^ { t }$ 且 $\omega _ { m _ { j + 1 } } ^ { t } ( k _ { j } ) = m _ { j }$ 。后一种情形

$$
k _ {j} \in d _ {m _ {j + 1}} \cap \mathrm{dom} \left(\sigma_ {m _ {j}} ^ {t}\right) \subseteq d _ {m _ {j + 1}} \cap p _ {m _ {j}}
$$

第二个成员资格是定理 63(3) 在 $m _ { j + 1 }$ 的 t 所在的片段处，因此 $m _ { j } \prec$ $m _ { j + 1 }$ 。再者 tar $\mathrm { g e t } _ { m _ { j + 1 } } ^ { \bar { t } } \neq \omega _ { m _ { j + 1 } } ^ { t }$ ：Unloading 纤维在定义 $\sigma _ { \gamma }$ 的并集之外，因此 $k _ { j }$ 在 $\gamma ^ { t }$ 处未提供或由非 $m _ { j }$ 的纤维提供。若 $m _ { j + 1 }$ 在 Active 或 Reloading 中，它就会属于被排除的四种之一，因此它在 Unloading 中且构造继续。$m _ { j }$ 是 ≺-递增的，因此由非环性两两不同，而 dom $\left( F ^ { t } \right)$ 有限，所以构造停止。

终止。两个断言界定 $S ( n )$

(A) 在 target<sup>t</sup> 恒为 $\omega ^ { * } ,$ 的最大区间上，至多 $K + 4$ 个步骤作用于 n。读表 1 的 $\theta _ { n }$ 列，从 $\mathsf { A c t i v e } ( - , \omega )$（$\omega \neq \omega ^ { * }$）纤维取一个 L-Leave 和一个 L-Unload，然后若 $\omega ^ { * } \neq \perp$ 取一个 L-Begin 和至多 len $( e _ { n } ) \leq K$ 次落地，若最后一次落地是 L-Raise 再加一个 L-Unload；从针对 n $\neq \omega ^ { * }$ 的 Reloading 它取一个 L-Divert 代替 L-Leave，从任何其他状态取该序列的后缀。区间内没有进一步的 L-Divert 或 L-Leave，L-Begin 写的 ω 本身就是 $\mathrm { t a r g e t } _ { n } ^ { t } = \omega ^ { * }$ ，而在 Active $( - , \omega ^ { * } )$ 、$\omega ^ { * } = \bot$ 时的 Inactive(⊥) 和 Inactive(⊥) 处根本没有规则适用。

(B) 若 target<sup>t</sup><sub>n</sub> ≠ target<sup>t+1</sup><sub>n</sub> 且步骤 t 作用于 $m ,$ 则 $m \prec n$ 或步骤 t 写 $\tau _ { n }$ 。由定义 46，target 的值是 $\tau _ { n }$ 和 $d _ { n }$ 各键提供者表的函数；提供者满足 $k \in \mathrm { d o m } ( \sigma _ { m } ) \cap d _ { n }$ 从而 $m \prec n ,$ ，而表只在作用其自身纤维的步骤处改变（引理 54(1)）。非环性在第一种情形给出 m $\neq$ n ，引理 $5 4 ( 5 )$ 的单调性每纤维只接纳第二种一次。

由 (A) 区间计数把 $S ( n )$ 界定为 $S ( n ) \leq ( K + 4 ) ( V ( n ) + 1 )$ ，由 (B) 每次 target 转向要么消耗严格 ≺-低于 n 的纤维的一步，要么是 $\tau _ { n }$ 允许的一次转向，因此 $\begin{array} { r } { V ( n ) \leq 1 + \sum _ { m \prec n } S ( m ) } \end{array}$ 。由于 ≺ 无环且 N 有限，递归

$$
B (n) := (K + 4) \left(2 + \sum_ {m \prec n} B (m)\right)
$$

良基并定义 B 使 $S ( n ) \leq B ( n )$ ；因此 $V ( n )$ 有限且 $\begin{array} { r } { \sum _ { n } S ( n ) \le \sum _ { n } B ( n ) } \end{array}$ 由 (1)，不可扩展的序列是静止的。 □

N 的有限性是假设而非推导，而组件上的一个条件交付它。宿主持有的组件是在任何东西运行前给定的有限多个程序，因此若没有组件能（无论多么间接地）注册一个注册自身之一实例的组件的纤维，注册形成有界深度的树，而 len $( e _ { n } ) \leq K$ 界定其分支。假设排除的是无界注册自身实例的组件。

目标记录提供纤维而非布尔，在第 4.2 节的单一来源纪律下两者驱动相同转移，键在那里只有一个可能的提供者。视图买来的是上面结果的词汇，定理 63 和定理 64 都谈纤维据以激活的解析，且它使那些结果在第 3.2.3 节的作用域解析下存活，在那里一个键在不同领域解析到不同提供者而提供不再迫使视图。实现携带该作用域并把视图保存在 fiber.committed 中（第 5.1.3 节）。

## 4.4.5. 合流性（Confluence）

迄今的结果关于单个纤维。刻画系统整体的性质是它的动态历史不留下痕迹：无论运行系统经历过什么激活与停用序列，它静止处的状态都是相同插入与退役会在每个最终激活的组件按依赖顺序各加载一次、且从不卸载时产生的状态。生命周期联系是合流的，它收敛的范式是静态装配的那个。对动态组合而言，这相当于增量计算 [45] 通过变更传播确立的与从头求值的一致性。

该断言只关于 ⟶。编排步骤是输入，给定不同输入的两个序列落在不同地方没有有趣的原因；关键在生命周期规则（对哪个纤维下一步以及 Reloading 纤维取哪个出口是非确定性的）能否被弄得不一致。

首先需要三个引理。第一个在不提及任何步骤序列的情况下固定最终 Active 的纤维集，这使它成为输入的函数而非调度的函数。

定义 67. 纤维在 γ 处是受支撑的（supported），当它未退役、注册它的纤维受支撑、且它声明的每个键都由受支撑的纤维提供。dom $\left( F _ { \gamma } \right)$ 上的支撑联系是这些条款读取的两个联系的并，

$$
m \triangleleft n := m \prec n \vee \pi_ {n} = m\tag{62}
$$

在其良基处（引理 68）我们写 A 为支撑集，即 γ 处受支撑的纤维：

$$
n \in A := \neg \tau_ {n} \land (\pi_ {n} = \operatorname{root} \lor \pi_ {n} \in A) \land \forall k \in d _ {n}. \exists m \in A. k \in p _ {m}\tag{63}
$$

其中 $\pi _ { n } = \mathfrak { r o o t }$ 标记编排器插入的纤维，$\pi _ { n }$ 否则是激活注册 n 的纤维。这些条款不读 $\tau , \pi , d , p$ 以外的字段。两半都把纤维关联到紧邻其下的一者，父而非祖先、直接提供者而非传递提供者，因为那是条款所读；下面的结果想要序时取传递闭包，其最小元、最大元和线性化是 ⊲ 的那些。

这些条款引用 A 本身，因此定义是沿 ⊲ 的递归，而下面使它成为有解的那个。

引理 68. （支撑良基。）令 ≺ 无环且 γ 由步骤序列达到。则 ⊲ 良基，且 A 是定义 $^ { 6 7 , }$ 的唯一解，一个只由 $\tau , \pi , d ,$ 和 p 决定且独立于步骤的函数。

证明. 按注册每个名字的步骤的索引对 dom $\left( F _ { \gamma } \right)$ 的名字排序，定义 53 通过让序列始于空注册表提供之。$\vartriangleleft$ 的父半部在该索引下降：O-Insert 以 $\pi \in \mathrm { d o m } \big ( F _ { \gamma } \big )$ 为前提，因此父指针命名较早注册的纤维，迭代它在有限步内到达名字的整个祖先。循环因此必须使用 $\prec ,$ 且因 ≺ 无环它必须混合两者，这需要某个 n 声明 $m \mathrm { { s } }$ 自身子树中的纤维可能提供的键。这样的纤维由 n 或 $m \mathrm { { s } }$ 后代之一的激活注册，因此在 $m ;$ 的 L-Begin 之后的步骤处注册；该 L-Begin 以 $\gamma \models d _ { m }$ 为前提，因此提供该键的纤维在那之前已 Active，而定义 58 的条款 (2) 不给该键第二个可能的提供者。将闭合循环的纤维因此从不被注册，该边不在 dom $\left( F _ { \gamma } \right)$ 中。良基递归有唯一解，而条款只读那四个字段。 □

最后一条款读 $p ,$ 即组件可能提供的键，而目标读 dom $\left( \sigma _ { \gamma } \right)$ ，即其纤维已安装的键，定义 43 以 dom $( \sigma _ { n } ) \subseteq$ $p _ { n }$ 关联两者。支撑集因此一般过度近似 Active 纤维，而闭合差距的条件如下。

定义 69. 组件 $( d , p , e )$ 在其提供上完备（total），当完成激活的它已安装 $p ,$ 的每个键，从而在每个实例化它的 Active 纤维处 dom $( \sigma _ { n } ) = p _ { n }$ 。

像独立性（定义 60）一样，这是只对组件成立的条件，不提及生命周期状态或步骤，而独立性已经界定它可能失败多远：若组件只在另一组件效应达到的上下文状态安装键，其正向映射就不会与该组件的交换，因此纤维安装的键由其组件而非调度固定。完备性所加的是固定集是全部 $p$ 而非其真子集。

引理 70. （静止处的支撑。）令 ≺ 无环、quiet $( \gamma )$ 、$\gamma$ 无纤维失败、且 $\gamma$ 的每个组件在其提供上完备（定义 69）。则支撑集是 Active 纤维集：

$$
A = \{n: \theta_ {n} = \text { Active } (-, -) \}\tag{64}
$$

证明. 写 $A ^ { \prime }$ 为右侧。由于无纤维失败，定义 49 的静止性只留 Inactive(⊥) 和 Active 作为状态并读

$$
n \in A ^ {\prime} \Longleftrightarrow \mathrm{target} _ {n} (\gamma) \neq \bot
$$

由定义 46 右侧恰在 $\neg \tau _ { n }$ 且每个 $k \in d _ { n }$ 位于 dom $\left( \sigma _ { \gamma } \right)$ 时成立，而 dom $\textstyle ( \sigma _ { \gamma } ) = \bigcup _ { m \in A ^ { \prime } } p _ { m }$ 由定义 69。中间条款是目标不再携带的，而注册提供它：$\pi _ { n } \neq$ root 的纤维只由 $\pi _ { n } ,$ 的激活注册，若 $\pi _ { n } \notin A ^ { \prime }$ 则 $\pi _ { n }$ 不 Active，因此其累加器已运行并由定义 $^ { 4 7 , }$ 退役 n，给出 $\tau _ { n }$ 。因此 $A ^ { \prime }$ 满足定义 $^ { 6 7 , }$ 的条款，而引理 68 给它们唯一解，所以 $A = A ^ { \prime }$ □

引理 71. （转置。）令步骤两两独立且 $F ^ { t }$ 良构，并令步骤 t 和 $t + 1$ 作用于不同纤维 n 和 m。

1. 若两者都应用激活规则（即 L-Begin、L-Iter 或 L-Finish）且步骤 $t + 1$ 在 $\gamma ^ { t }$ 处适用，则步骤 t 在步骤 $t + 1$ 从 $\gamma ^ { t }$ 产生的状态处适用，且两个顺序达到相同的 $\gamma ^ { t + \bar { 2 } }$

2. 若步骤 t 在 $m ,$ 处应用激活规则、步骤 $t + 1$ 在 $n ,$ 处应用编排规则且步骤 t 不注册 $n ,$ 则两者同样成立。

证明. 对 (1)，由表 1，n 的步骤写 $\theta _ { m }$ 并在 $\Psi ^ { t } \in \mathfrak { M } ( e _ { m } ) .$ 内写表 $\sigma _ { m }$ 和效应部分。它因此让 $\theta _ { n }$ 和 $i _ { n }$ 独处，并由定义 60 的第二条件让 $i _ { n }$ 产生的逆和续延也独处，因此只需检查步骤 $t + 1$ 提及 $\mathrm { t a r g e t } _ { n }$ 的前提。其退役半不会失败，没有激活规则写 $\mathrm { ~ a ~ } \tau .$ 。其解析半也不会移动：步骤 $t + 1$ 在 $\gamma ^ { t }$ 处适用使每个 $k \in d _ { n }$ 在 dom $\scriptstyle ( \sigma ^ { t } )$ 中，而定义 58 的条款 (2) 使提供这样的 k 的纤维成为唯一能提供的，因此 k $\notin \boldsymbol { p } _ { m }$ 且 $\sigma _ { m }$ 的写入不达 $d _ { n }$ 的键。反方向的同一论证使步骤 t 适用。最后 $\Psi ^ { t } \in \mathfrak { M } ( e _ { m } )$ 和 $\Psi ^ { t + 1 } \in \mathfrak { M } ( e _ { n } )$ 由定义 60 的第一条件交换，而两个编辑写不同纤维的控制字段，因此复合在任一顺序相同。

对 (2)，编排步骤由表 1 有 $\Psi ^ { t + 1 } = \mathrm { i d } _ { \Gamma }$ ，因此两个状态映射无条件交换，而其 edit<sup>t+1</sup> 只写 $n ,$ 的 $\tau _ { n }$ 或 dom $\left( F _ { \gamma } \right)$ ，激活步骤既不读也不写：后者的前提读 $\theta _ { m } , i _ { m } , \tau _ { m } ,$ 和 $\mathrm { t a r g e t } _ { m } ,$ 而新 n 的 O-Insert 不移动目标，新纤维不提供任何东西，而 n 的 O-Retire 或 O-Remove 使 $\sigma _ { \gamma }$ 留在原处，n 在前一种情形 Inactive 后一种情形表不受影响。因此步骤 t 保持适用。反之，编排步骤的每个前提要么在 $n ,$ 处读出（步骤 t 不写），要么是较小注册表只会放松的 O-Insert 的两个前提之一，其在 $\gamma ^ { t + 1 }$ 的适用性给出其在 $\gamma ^ { t } .$ 的适用性；这里步骤 t 不注册 n 是使 n 在 O-Retire 和 O-Remove 所需的 $\gamma ^ { t }$ 处在场的东西。 □

引理 72. （删除。）令步骤序列两两独立、每个组件在其提供上完备（定义 69）、它达到无纤维失败的静止 $\gamma ^ { T }$ 、$[ b , u ]$ 是闭合的 n 的片段、序列中没有满足 $n \prec m$ 的 m 的片段闭合、且 n 在 $[ b , u ]$ 注册的任何纤维没有片段。写 R 为那些注册抽取的名字。则删除 $[ b , u ]$ 中作用于 n 的步骤、连同作用于 R 中名字的每个步骤，留下一个达到与 $\gamma ^ { T }$ 状态 ≈-相等、在 R 之外 ≃-相等的状态的步骤序列。

证明. 被删除的步骤让状态留在它们发现它的地方。令 $t _ { 1 } < \cdots < t _ { l }$ 为 $[ b , u ]$ 中作用于非 n 纤维的步骤。推论 62 读

$$
\gamma^ {u + 1} \approx \left(\Psi^ {t _ {l}} \circ \dots \circ \Psi^ {t _ {1}}\right) \left(\gamma^ {b}\right)
$$

其右侧正是 $[ b , u ]$ 中存活的步骤自己产生的，$\gamma ^ { b - 1 } \approx \gamma ^ { b }$ 且其编辑写删除未触及的非 n 纤维的控制字段。由表 1，n 的被删除步骤只写 $\theta _ { n } ,$ 引理 $5 4 ( 4 )$ 在 $u ,$ 处把它恢复到 Inactive(⊥)（无纤维失败），且它在 $\gamma ^ { b - 1 }$ 持有它。

一个不变量携带后缀。写 $\gamma ^ { \prime t }$ 为存活步骤在对应 n 的点达到的状态。我们断言，对每个 $t > u ,$ 有 $\gamma ^ { t } \approx \gamma ^ { \prime t }$ 、n 的每个名字在 $\gamma ^ { t }$ 处残余且在 $\gamma ^ { \prime t }$ 处缺席、且两个状态在 n 外每个名字的每个字段上一致。在 $t = u + 1$ 处这是上面一段连同定义 $4 7 ,$ ，后者使 n 的每个名字被 n 处运行的累加器退役，Inactive(⊥) 且持有空表，n 的纤维按假设没有片段。归纳步是对 n 的每个名字依次应用引理 $5 7 ( 1 )$ ：作用于 n 外的步骤在两个状态有相同前提、达到再次 ≈-相等的状态、并使 n 的条目保持残余。作用于 n 中名字的步骤是被删除者之一，而引理 $5 7 ( 2 )$ 是它必须被删除而非保留的原因，缺席名字的 O-Retire 或 O-Remove 没有纤维可作用；由 (1) 又知这样的步骤不移动 $R ,$ 外的字段，因此丢弃它保持不变量。因此最终状态 ≈-相等，且在 n 外相等。

没有存活步骤失去前提。作用于 m $\not \in R \cup \{ n \}$ 的步骤只通过 $\mathrm { t a r g e t } _ { m } ( \gamma )$ 或 relied $_ m ( \gamma )$ 读 n 。前者在 n 声明 m 提供的键时依赖 m ，从而 $n \prec m ,$ 在 n 注册 $m ,$ 时依赖 n ，这使 $m \in R .$ 。第一种情形 n 的片段按假设不闭合，因此它在 $\gamma ^ { T }$ 处打开，那里 quiet 给出 $\omega _ { m } = \mathrm { t a r g e t } _ { m } ^ { T }$ 而引理 70 把其值放在 Active 纤维中，n 不是；由于键至多有一个可能的提供者，n 在 n 的 L-Begin 处也没提供 $d _ { m }$ 的任何键。第二种只通过 $\omega _ { n }$ 的值读 n ，而删除片段只能使 relied 变假，这放松 L-Unload 的守卫而非阻塞它。这样的步骤读 n 中名字的东西由不变量覆盖。两两独立是效应函数的性质，删除步骤保持它。 □

定理 73. （合流性。）令步骤序列达到无纤维失败的静止 $\gamma ^ { T }$ 、步骤两两独立且每个组件在其提供上完备（定义 69）、A 如定义 $6 7$ 。则

1. （规范形。）$\gamma ^ { T }$ 是从 $\gamma ^ { 0 }$ 经一个序列达到的（在还原撤出的名字条目之上），该序列以原始顺序采取相同的编排步骤，编排器插入的纤维处的那些步骤先于每个生命周期步骤、其余每个随后跟随注册其所作用纤维的步骤，并且对线性化 ⊲ 的 A 的枚举 $n _ { 1 } , . . . , n _ { k }$ 按该顺序各取一个 $n _ { i }$ 的片段。

2. （合流性。）任何两个从 $\gamma ^ { 0 }$ 采取相同编排步骤的此类序列达到的状态在引理 56 式的重命名后由 ≃ 和 ≈ 相关。

证明. 对 (1)，序列的片段有两种：闭合的以及仍开在 $\gamma ^ { T }$ 的，后者由 quiet<sup>t</sup> 和引理 70 是 A 每个纤维的一个片段。

闭合片段先走，对其数量归纳。每阶段在片段仍闭合的纤维中选一个其纤维 ⊲-最大的闭合片段；一个由引理 68 和 A 的有限性存在。引理 72 的三个假设于是满足。没有满足 $n \prec m$ 的 m 有闭合片段，由最大性。n 在 [b, u] 注册的任何纤维没有片段：这样的纤维被 n 处运行的累加器退役（定义 47）并由引理 54(5) 保持退役，因此其目标视图是 ⊥ 而引理 70 把它放在 A 外，从而它在 $\gamma ^ { T }$ 处没有打开的片段；且 ⊲ 通过其父指针把它关联到 n，因此由最大性它也没有闭合的。引理移除该片段连同它注册名字的步骤，把 $\gamma ^ { T }$ 留在原处（那些名字之上）。度量减一，因此没有闭合片段剩余。

A 外的纤维不取生命周期步骤。它在 $\gamma ^ { T }$ 处没有打开的片段（由引理 70 和 quiet<sup>t</sup>），现在也没有闭合的，因此它完全没有片段、全程 Inactive(⊥)；L-Begin 是那里唯一适用的规则，而应用它会打开片段。

编排步骤随后。编排器插入的纤维处的编排步骤经引理 71(2) 移到一个更早的位置、越过不同纤维的生命周期步骤，该引理适用因为 A 纤维的步骤不注册这样的名字：注册抽取新名，而这里的名字是原始序列的 O-Insert 引入的。与同一纤维的生命周期步骤则无可交换，n 的 O-Insert 已先于 n 的每个步骤，而 n 的 O-Retire 或 O-Remove 只在 A 外应用，后者不取生命周期步骤。逐一把每个移到前面保持其相对顺序。某激活注册的纤维处的编排步骤不能移到前面，其前提要求该纤维在场，因此它留在注册放它的地方；由上面一段它作用于 A 外，因此由引理 71 的同一条款它与它和注册之间的一切交换。

片段被排序并做成连续的，对 $| A |$ 归纳。令 $n _ { 1 }$ 在 A 中 ⊲-最小。则 $d _ { n _ { 1 } } =$ $\emptyset$ 且 $\pi _ { n _ { 1 } } = \mathsf { r o o t } ,$ 因为定义 $6 7$ 把 $d _ { n _ { 1 } }$ 键的提供者和注册 $n _ { 1 }$ 的纤维放在 A 中而 ⊲ 把两者都放在 $n _ { 1 }$ 下。因此 targe $\mathrm { t } _ { n _ { 1 } }$ 不读另一纤维的字段，且没有编排步骤剩下写 $\tau _ { n _ { 1 } }$ 、没有 $n _ { 1 }$ 下的纤维剩下退役它，故恒定。每个作用于 $n _ { 1 }$ 的步骤都是激活步骤，没有片段闭合，其剩余前提读 $\theta _ { n _ { 1 } }$ 和 $i _ { n _ { 1 } }$ ，由表 1 只有 $n _ { 1 }$ 写；每个因此在前面的每个状态处适用，而引理 71 在不移动端点的情况下把它移前一位。每次应用使 $n _ { 1 }$ 的步骤之前的其他纤维步骤数减一，因此 $n _ { 1 }$ 的片段成为初始连续块。该论证在块的后续后缀上对 $A \setminus \{ n _ { 1 } \}$ 重复，$n _ { 1 }$ 在那里全程 Active 且不取进一步步骤，因此它也贡献恒定目标。此产生的枚举按构造线性化 ⊲。

对 (2)，两个序列都经 (1) 化到规范序列，而两个还原在同一 A 上运行（重命名之下）。定义 67 读 $\tau , \pi , d ,$ 和 $p ,$ 其中后三个随纤维条目写一次（引理 $5 4 ( 5 ) )$ ），因此需要看到的是相同的名字带着相同的 $d , p ,$ 和 $\pi ,$ 产生、相同的名字被退役。两个序列按假设共享插入。它们也共享注册：A 纤维的激活在其每次迭代注册迭代器在那里命名的组件，定义 60 的第二条件在交错下保持它固定，因此 A-纤维下注册的树是该纤维组件的函数；那些注册抽取的名字不共享，而这里应用引理 56，用双射匹配两棵树。而退役要么是共享的编排步骤，要么是累加器采取的 O-Retire，后者恰好退役相同激活注册的名字。线性化 ⊲ 的两个枚举只差不可比片段之转置，引理 71 又使端点不变，因此两个规范序列一致。与定理 66 的终止一起，生命周期联系因此有唯一规范形。 □

失败被排除在声明之外，因为它是真正的分歧来源，而演算不应被读作否认它：步骤是否抛错取决于它运行针对的状态，因此一个调度可能使纤维失败而另一个完成它，两个静止状态随后在该纤维的生命周期状态上不同。它们在其他任何东西上不不同，由推论 62，它把失败纤维对状态的贡献置零。

在第 4.2 节的基础演算中，相同定理成立，而证明除了去掉一个条款外无需替换。L-Unload 在那里不携带守卫，因此引理 $7 2$ 的最后一段是空洞的；该引理其余部分只诉诸 quiet<sup>t</sup> ，基础演算原样提供。

该定理是允许把 Cordis 应用当作静态装配来推理的东西。添加组件、移除它、替换提供者、再逆转替换的编排器被保证到达它通过在一开始写下最终组合本应得到的状态，而推理哪些余效应在作用域内的组件作者可以只推理静止状态。它也划出保证的界限：它谈状态，不谈系统沿途产生的排放，这正是第 6.1 节在边界内跟踪的获取与跨越它的排放之间划的区分。

## 5. 实现与案例研究（Implementation and Case Study）

本节介绍 Cordis，它把第 3 节的诸形式模型实现为一种实用的编程抽象。Cordis 是一个时空可组合性的元框架：与针对特定领域（如 Web 路由、ORM、UI 渲染）的应用框架不同，它不规定任何具体场景；其唯一职责是提供通用的动态组合语义。实现分三层：(1) 核心库（第 5.1 节）直接实现效应与余效应系统；(2) 组件加载器（第 5.2 节）用配置协调与热模块替换扩展核心；(3) 像 Koishi（第 5.3 节）这样的应用框架在前两层之上构建领域特定功能。

## 5.1. 核心库（Core Library）

表 2 总结了理论构造与其运行时对应物之间的对应关系。特别地，我们在本节通篇使用下面引入的运行时名称，把理论符号保留给形式对应。我们也写作 @@name 表示框架内部符号键，因此 ctx[@@store] 中的方括号表示对上下文中一个不透明槽的符号键访问，而不是索引进一个字符串键映射。

| 理论（第 3 节、第 4 节） | 实现 |
| --- | --- |
| $\Gamma_{\infty}$ | ctx，一等上下文 |
| $\gamma \in \Gamma$ | 上下文树连同运行系统所触碰的一切 |
| $\mathfrak{E}_{\Gamma}, \mathfrak{E}_{\Gamma}^{\text{iter}}$ | 返回/产出逆的效应回调 |
| $effect_{\Gamma}(e)$ | ctx.effect(callback) |
| $\Sigma, \Sigma^{\text{iso}}, \Sigma^{\text{inter}}$ | ctx[@@store], ctx[@@isolate], ctx[@@intercept] |
| $get(k), set(k,v)$ | ctx.get(key), ctx.set(key, value) |
| $isolate(k,r)$ | ctx.isolate(key, realm) |
| $intercept(k,\nu)$ | ctx.intercept(key, metadata) |
| $\langle d,p,e,\pi,\sigma,\tau,\theta\rangle$ | fiber，$\mathfrak{C}_{\Gamma}$ 中一个组件的实例化 |
| $dom(F_{\gamma})$ | 通过 ctx.registry 枚举 |
| $n : \mathfrak{N}$ | fiber.uid |
| $d : \mathfrak{D}_{\Gamma}$ | fiber.inject |
| $p : \mathfrak{P}_{\Gamma}$ | 组件的 provide |
| $e : \mathfrak{E}_{\Gamma}^{*}$ | fiber.apply |
| $\pi : \mathfrak{N}$ | fiber.parent.fiber.uid，拥有其被实例化所在上下文的纤维 |
| 派生实现（定义 27） | fiber.ctx，纤维运行所在的子上下文 |
| $\theta$  （定义 44） | fiber.state，生命周期状态，其 LOADING 即 Reloading、其 FAILED 即 Inactive( $\xi$ ) |
| recover、累加器 g | fiber.dispose，累加器 |
| $\omega$  （定义 44） | fiber.committed，已提交视图 |
| $provider_{k}(\gamma)$ | 其提供者纤维为 ACTIVE 的一个 Impl |
| $target(\gamma,n)$ | fiber.target，由 refresh（算法 5）重算，其中 $\perp$ 即 INACTIVE |
| Future、惯性（第 4.3.3 节） | fiber.inertia，飞行中转移的句柄 |
| O-Insert、O-Retire（定义 47） | ctx.use 与其回调的逆（算法 4） |
| O-Remove | 从运行时丢弃的纤维，uid 被清除 |
| L-Begin、L-Iter、L-Finish | execute 的迭代循环（算法 1） |
| L-Divert | 迭代边界处守卫失败（算法 1），或 reload 链入 unload |
| L-Leave | refresh 把纤维标记为 UNLOADING（第 10 行） |
| L-Unload | unload 及其惯性链（算法 5） |
| L-Unload 上的守卫 | unload 等待被通知的依赖方（第 25 行） |
| L-Raise | 记录在纤维上的错误，其 target 被设为 $\perp$ |

表 2 | 理论到实现的对应

本节的其余部分自下而上构建核心库。第 5.1.1 节实现可逆效应，即上下文被修改所经由的唯一原语；第 5.1.2 节在其上实现响应式余效应；第 5.1.3 节把两者组合成组件生命周期；第 5.1.4 节暴露建立在其上的上下文级操作。

## 5.1.1. 效应跟踪（Effect Tracking）

本节实现可逆效应（第 3.1 节）。Cordis 中的每个上下文修改都流经一个唯一原语 ctx.effect：余效应提供、组件实例化以及每个其他修改上下文的操作都归结为一次 ctx.effect 调用，因此任何经上下文执行的操作都会被自动跟踪并在组件卸载时被恢复。操作上，ctx.effect 是 effect<sup>iter</sup>（定义 52）的实现：它接受一个类型为 $\mathfrak { E } _ { \Gamma } ^ { \mathrm { i t e r } }$ 的回调，并将其提升到 ${ \mathfrak { E } } _ { \partial \Gamma } ^ { \mathrm { i t e r } }$ ，产生一个 dispose 闭包，该闭包在被调用时恢复该效应。Cordis 通过这一个操作同时接受 $\mathfrak { E } _ { \Gamma }$ 和 ${ \mathfrak { E } } _ { \Gamma } ^ { \mathrm { i t e r } }$（临时多态）；我们以迭代器形式为代表，因为普通效应函数是产生单个逆的退化迭代器。该操作不检查的是 ${ \mathfrak { E } } _ { \Gamma } ^ { * }$ 所携带的见证：回调提供一个逆，而该逆恢复其所伴随的效应是对组件作者的义务，而非运行时验证的性质。定理 61 是演算诉诸它的地方，第 6.1 节是对该义务加以界定的地方。

算法 1 展示 ctx.effect 的构造。我们写 $f \circ g$ 表示先运行 $g$ 再运行 $f$ 的处置器，id 表示无操作；因此前置每个新逆会产生 LIFO 恢复。

```txt
Algorithm 1 Effect tracking
1 async function execute(callback, guard)
2 iter ← callback()
3 inverse ← id
4 while guard()
5 (value, done) ← await iter.next()
6 if value then inverse ← value ○ inverse
7 if done then break
8 return inverse
9 function effect(ctx, callback)
10 armed ← true
11 task ← execute(callback, () → armed)
12 async function dispose()
13 if not armed then return
14 armed ← false
15 recover ← await task
16 recover()
17 ctx.dispose ← dispose ○ ctx.dispose
18 return dispose
```

引擎 execute 把回调作为效应迭代器 $( { \mathfrak { E } } _ { \Gamma } ^ { \mathrm { i t e r } }$ ，定义 51）驱动，并把每一步产出的逆折叠进单个复合逆中。每一步之前它查询一个调用方提供的守卫；一旦守卫触发，迭代停止，只保留迄今累积的逆。这是第 4.3.2 节的步边界中断：Maybe $( \mathfrak { E } ^ { \mathrm { i t e r } } )$ 续延由迭代器的 done 标志连同守卫实现。

ctx.effect 是 execute 之上的一个薄包装，它添加两样东西。第一，自处置：守卫报告 armed 标志，返回的 dispose 把 armed 翻转为 false，这同时中止任何飞行中的迭代并使恢复至多触发一次。触发两次会在没有任何效应应用产生的状态处应用逆，那里没有东西约束它恢复任何东西。第二，父组合：dispose 被前置到包围它的上下文所累积的逆 ctx.dispose 上，因此子效应的逆本身是父上的一个效应，这正是 $\partial ^ { 2 } \Gamma$ 的递归结构。组件级（第 5.1.3 节）复用同一个 execute，其守卫测试 fiber.target 的稳定性而非 armed。

## 5.1.2. 余效应操作（Coeffect Operations）

本节实现响应式余效应（第 3.2 节）。所有余效应操作作用于每个上下文携带的三个符号键槽：

• @@store：值存储 $\sigma : ( r : R ) \to \mathcal { V } _ { r }$ ，从领域符号到类型化值；

• @@isolate：领域表 $\rho : \mathrm { M a p } ( K , R )$ ，从余效应键到领域符号；

• @@intercept：拦截表 $\iota : ( k : K ) \to { \mathcal { M } } _ { k }$ ，把每个键分配其元数据。

前两者组合成两层解析 $k \to \rho ( k ) \to \sigma ( \rho ( k ) )$ ：ctx.get(key)（算法 2）从 @@isolate 读取领域符号 $\rho ( k )$ ，然后从 @@store 读取绑定值 $\sigma ( \rho ( k ) )$ 。$\rho$ 间接层让隔离把一个键重定向到独立绑定，而 @@intercept 只在访问绑定时才被查询，调整它如何使用而非它解析到什么。我们分两部分实现这些操作：(1) 提供与通知，安装或撤除绑定并把变化传播给依赖方；以及 (2) 隔离与拦截，重塑一个键如何解析。

提供与通知。由于 set $( k , v )$ 具有类型 $\mathfrak { E } _ { \Sigma }$ （第 3.1 节），余效应提供是一次 ctx.effect 调用并继承其自动跟踪与恢复。算法 2 实现 ctx.set(key, value)，即具体的 set $( k , v )$ ：回调把值在领域符号 $\rho ( k )$ 下绑定进存储，返回的 dispose 函数移除它。安装与移除都调用 notify 把变化传播给依赖组件。

```txt
Algorithm 2 Coeffect operations
1 function get(ctx, key)
2    realm ← ctx[@@isolate][key] ▷ ρ(k)
3    return ctx[@@store][realm] ▷ σ(ρ(k))
4 function set(ctx, key, value)
5    function callback()
6    realm ← ctx[@@isolate][key] ▷ ρ(k)
7    ctx[@@store][realm] ← value ▷ σ[ρ(k) ↦ v]
8    notify(ctx, [key])
9    return function()
10    delete ctx[@@store][realm] ▷ σ \ ρ(k)
11    notify(ctx, [key])
12    return ctx.effect(callback)
```

算法 3 通过为每个存活纤维测试已改变的键是否出现在其 fiber.inject 中并解析到同一领域，把每次绑定变化传播给依赖方；若如此，它调用 refresh（第 5.1.3 节）对照新状态重新求值该纤维，并返回它重新求值的纤维，以便调用方能等待它们。这是定义 26 的响应式分类：使满足性翻转的变化激活或停用纤维，而 refresh 的幂等性使中性变化无害。这种重新求值与多种控制流的相互作用在第 5.1.3 节展开。

```txt
Algorithm 3 Reactive notification
1 function notify(ctx, keys)
2    affected ← ∅
3    for fiber in all_fibers do
4    for key in keys do
5    if key ∈ fiber.inject and fiber ctx[@@isolate][key] = ctx[@@isolate][key] then
6    refresh(fiber)
7    affected ← affected ∪ {fiber}
8    break
9    return affected
```

一个绑定只在安装它的纤维是 ACTIVE 时才对依赖方算作可用，因此 refresh 对照活跃提供者而非仅对照存储解析每个声明键。这是定义 46 的 provided-by 关系，也是使撤出在发生前一步就对依赖方可见的东西：已进入 UNLOADING 的提供者已停止提供，因此其依赖方重算出一个不满足的目标视图并在其绑定仍全部在位时开始自己的拆卸。

隔离与拦截。这两个操作在结构上做同一件事：每个都派生一个子上下文，为一个键调整一个继承的表，让父上下文原封不动，因此恢复是隐式的：丢弃子上下文即可，无需运行显式逆。ctx.isolate(key, realm) 用 realm（默认新生成的符号）覆盖领域映射 ρ（实现 isolate，定义 29），因此把不同符号赋给同一键的两个上下文解析到独立绑定。ctx.intercept(key, metadata) 把 metadata 合并进拦截表 ι（实现 intercept，定义 31）：依该定义，新元数据与上下文为 key 已经携带的任何东西组合并对其优先。

## 5.1.3. 组件生命周期（Component Lifecycle）

组件经 ctx.use 被实例化为一个纤维。本节把（第 5.1 节引入的）纤维作为第 4.3.3 节的惯性状态机赋予操作意义。两个字段驱动下面的算法：fiber.parent，fiber.ctx 的父上下文，它形成组件层级（$\Gamma _ { \infty } ,$ 第 3.3.1 节的递归结构），以及 fiber.inertia，飞行中异步转移的句柄（空闲时为 null）。

算法 4 展示组件实例化。一个组件把余效应规范 component.inject（d）与效应函数 component.apply 配对；实例化把组件的 config 绑定进 fiber.apply（第 9 行），即生命周期随后运行的经配置应用的效应函数（e）。回调函数（第 2 行）是父纤维中跟踪的效应：被执行时，它通过调用 refresh（算法 5）启动子组件的生命周期；被恢复时，它迫使子的 target 为 ⊥ 并触发 unload。这是定义 47 的注册原语，以 callback 为其 O-Insert、以 callback 返回的闭包为其 O-Retire：一次实例化是父的一个普通跟踪效应，因此卸载父会级联到其子。

```txt
function callback()
    refresh(fiber)
    return function()
    fiber.target ← ⊥
    unload(fiber)

fiber ← Fiber(parent: ctx, inject: component.inject)
fiber.ctx ← ctx[fiber → fiber]
fiber.apply ← () → component.apply(fiber.ctx, config)
ctx.effect(callback)
return fiber
```

算法 5 实现第 4.3.3 节的惯性状态机，其中 reload 和 unload 是惯性的：一旦进入，一次转移运行到完成，之后系统才响应目标状态变化。它使用余效应存储上的两个辅助查询：resolve(inject) 返回声明键当前解析到的绑定，provided(fiber) 返回该纤维安装其绑定的键。refresh 函数从余效应存储重算 fiber.target，并且若纤维尚未处于转移中，则启动一个 reload 或 unload 任务<sup>2</sup>。reload 函数记录当前目标并执行组件的效应函数 apply。完成后，它检查目标是否仍匹配：若匹配，纤维进入 ACTIVE；若不匹配（无论新目标是 ⊥ 还是不同的提供者集），它链入 unload。对称地，unload 以 LIFO 顺序恢复所有被跟踪的效应，然后进入 INACTIVE 或链入 reload。这种互递归实现惯性性质：一旦一次转移开始，它在任何新转移能开始之前完成。

```txt
Algorithm 5 Component lifecycle

1 function refresh(fiber)
2 target ← target(γ, n)
3 if target = fiber.target then return
4 fiber.target ← target
5 if fiber.inertia then return
6 if target ≠ ⊥ then
7    fiber.state ← LOADING
8    fiber.inertia ← create_task(reload(fiber))
9 else
10    fiber.state ← UNLOADING ▷ out of service before any inverse is scheduled
11    fiber.inertia ← create_task(unload(fiber))
12 async function reload(fiber)
13 target₀ ← fiber.target
14 fiber.committed ← resolve(fiber.inject) ▷ commit the view
15 recover ← await execute(fiber.apply, () ↦ fiber.target = target₀)
16 fiber.dispose ← recover ∘ fiber.dispose
17 if fiber.target = target₀ then
18    fiber.state ← ACTIVE
```

```txt
19 | notify(fiber.ctx, provided(fiber))
20 | fiber.inertia ← null
21 else
22 | fiber.state ← UNLOADING
23 | fiber.inertia ← create_task(unload(fiber))
24 async function unload(fiber)
25 await all.notify(fiber.ctx, provided(fiber)).map(f → f.await())) ▷ drain dependents
26 await fiber.dispose()
27 fiber.dispose ← id
28 fiber.committed ← ⊥
29 if fiber.target = ⊥ then
30 | fiber.state ← INACTIVE
31 | fiber.inertia ← null
32 else
33 | fiber.state ← LOADING
34 | fiber.inertia ← create_task(reload(fiber))
```

fiber.target 通过对照当前余效应存储解析每个声明键并元组化提供它的纤维的 uid 来计算，因此它是 target(n, γ)（定义 46）的一个摘要。用提供者而非其值来识别绑定，是使对已记录目标的一次比较即足够的东西：uid 是全新抽取且永不重用的，因此被替换的提供者不能被误认为替换它的那个，即使两者提供相等的值。由于 notify（第 5.1.2 节）在每次余效应变化时重算目标，一个纤维恰在其声明键之一改由不同纤维提供时重新加载。因此，在其原位覆写自身绑定的提供者不被观察到；想让其替换传播的组件会撤出绑定并全新安装它。

该算法在两个互补的层面运作。在转移层面，reload 和 unload 在完成时检查目标，使惯性链能够跨越转移。在每个转移内部的迭代层面，效应执行（算法 1）在每次迭代边界检查目标，使单次转移内的部分回滚成为可能。这两个机制分别对应第 4.3.3 节的转移间链接与定理 64 所依赖的转移内过期检查。

三行承载定理 63 的余效应排序，而每一行所在的位置正是使排序成立的东西。reload 在第 14 行提交解析视图，unload 只在每个逆都运行之后才丢弃它，因此只要纤维被加载（包括其自身的拆卸），它就读到相同的绑定。refresh 在转移任务创建之前于第 10 行把纤维标记为 UNLOADING，即 L-Leave 步骤：纤维停止提供，依赖方在其任何逆被调度之前据此重算。unload 随后在第 25 行等待每个被通知的依赖方到达 INACTIVE，即 L-Unload 上的守卫；notify 只在依赖方的声明键解析到与提供者相同的领域符号时才接纳它，这是守卫之要求的运行时形式，即依赖方从该纤维看到键而非仅仅声明它。等待位于整个恢复之前而非被等待的某个逆内部，因为 fiber.dispose 并发启动一个纤维的效应，而置于其中之一内的等待会让其余部分失去排序。终止遵循定理 66：一个纤维只等待那些已停止可满足的依赖方，而自身是提供者的依赖方对其自己的依赖方以同样方式等待，因此提供者图按需遍历而非预先分析。

## 5.1.4. 上下文访问（Context Access）

第 5.1.2 节的余效应操作构成一个反射式 API：余效应用 ctx.set(key, value) 写入、用 ctx.get(key) 读取，两者都按键名。Cordis 在此反射式 API 之上叠加第二种更原生地扩展与消费上下文的方式：属性访问。组件可以把余效应作为属性 ctx[key] 访问，就像它是上下文的原生结构，而非经由方法调用。在 TypeScript 中，Cordis 用 get 陷阱中介每次属性访问的 Proxy 实现这一点。算法 6 展示上下文如何在第 5.1.2 节的原语 get 之上把这样的访问解析为一个余效应。

```txt
Algorithm 6 Proxy-mediated context access
1 function resolve(ctx, key)
2 fiber ← ctx.fiber
3 repeat
4 if key ∈ fiber.committed then return fiber.committed[key]
5 if key ∈ fiber.inject then throw INACTIVE_ACCESS
6 if fiber = root then throw UNDECLARED_ACCESS
7 fiber ← fiber.parent.fiber
```

算法 6 从访问上下文沿纤维链向上走：在已提交视图绑定 key 的第一个纤维处，访问被授权并返回该绑定；若走到一个声明了 key 而未提交它的纤维，则纤维未加载且访问失败；若到达根而无任何声明，则访问被拒为未声明。这正是 proxy 与裸 ctx.get 不同之处：ctx.get(key) 是对存储的一次查询，返回绑定值或什么也不返回且从不失败，而 proxy 对照访问纤维自身的视图解析并强制使用点的余效应规范 d。读取视图而非存储也是定理 63 所依赖的，因为正是它让依赖对因该依赖消失而触发其拆卸的组件仍可读。

这种拒绝是访问点执行的一次运行时检查。由于组件的余效应规范 d 是静态声明的，同样的违反原则上可在编译期检测，通过在执行前把每个 ctx[key] 对照声明的 d 解析；第 6.4 节讨论宿主语言的类型级依赖声明与编译期元编程如何能恰好执行这种中介。

## 5.2. 组件加载器（Component Loader）

核心库为组件开发者装备了动态组合的命令式原语，如 ctx.effect、ctx.use 和 ctx.set。应用编排者面临一个独立的问题，他们把预先存在的组件组装成运行系统并在其生命周期内调整组合。组件加载器通过引入一个声明式配置层解决这个问题：编排者把期望的组合指定为持久数据结构，加载器把对该规范的变化翻译成相应的命令式纤维操作。

## 5.2.1. 声明式配置（Declarative Configuration）

第 4 节把运行系统分解为纤维，每个纤维是一个组件的一次实例化。一次实例化所需的一切都可以声明，因此编排者可以把整个系统描述为一个声明式配置：一个加载器实现为纤维并与之保持同步的持久记录。

条目。一个配置由条目组成。每个条目指定一个纤维并管理它，而绑定双向运行：加载器通过调整纤维响应条目字段的变化，而修订自身配置或禁用自身的组件会把变化写回其条目。

定义 74. 一个条目声明单个纤维，记录：

• id —— 稳定标识符，其组的子列表改变时用作协调键；

• url —— 要实例化的组件模块的 URL；

• isolate —— 应用到条目上下文的隔离注解；

• intercept —— 应用到条目上下文的拦截注解；

• config —— 绑定进组件以形成其效应函数 apply 的配置；

• disabled —— 条目是否被管理上关闭。

一个条目可以作为忠实的规范，因为支撑一个纤维的东西恰好是条目记录的东西。定义 67 的支撑集只读 $\tau , \pi , d ,$ 和 p 而不读别的，而一个条目给出全部四个：disabled 给出 τ，树中条目的父给出 π，url 选择声明 d 和 p 的组件。支撑集留下不读的字段是纤维的运行时状态，一次实例化也不需要它，而引理 70 在每组件安装它声明的每个键（定义 69）之处把支撑集与静止状态（定义 49）的 Active 纤维等同。

这些条目形成一个配置树，即系统加载什么的可信记录。一个条目可以是映射到单个纤维的叶子，或其组件可以转而加载更多组件，使条目成为分支节点。Cordis 为这种分组与嵌套加载提供组件：@cordisjs/group 把一个子条目列表作为其配置并把它们作为子组加载，@cordisjs/include 加载一个外部配置文件（YAML 或 JSON）并把其条目作为嵌套子树嫁接进来。两者都是建立在定义 47（算法 4）的注册原语之上的普通组件，因此一棵嵌套树保持在演算之内且下面的结果对之成立。

协调。当一个条目的记录变化时，加载器增量协调而非拆毁纤维并整体重建。这样协调是健全的，原因由元理论提供。

• 定理 73 使静止状态成为仅最终配置的函数：无论加载器沿途执行什么实例化与退役、以什么顺序，系统都在从零加载最终配置本应达到的地方静止。最终哪些组件被加载只按声明读出，只要每组件安装它声明的每个键（定义 69）；只把某键在某些配置下声明并安装的组件，加载器仍可协调，但加载的组件集随后也应答那些配置。

• 定理 66 证明系统确实静止，因此一旦其实例化与退役已发出，一次协调即完成。

• 推论 62 把离开的纤维对状态的贡献置零，因此重建一个条目撤出它的纤维所安装的、让周围纤维保持原状。

• 定理 63 让条目一起实例化，编排者无需安排加载顺序：声明键尚未被提供的纤维在其 L-Begin 处等待，而提供者离开的那个在它之前被停用。依赖因此约束纤维何时激活而非何时取回并求值其模块，所以加载器并发加载模块，拉起大型配置的时间花在那里。

在条目声明的纤维之上，加载器按条目的哪个字段变化分派，并为每个应用扰动最小的操作。

• id、url —— 重建条目，因为其身份或其组件已变；

• isolate —— 重分配条目的领域（算法 7）；

• intercept —— 原位更新，因为拦截元数据在读取时被查询且无需重新加载；

• config —— 交给组件，组件决定如何应用新载荷，通常把它与先前的 diff 并只在实质变化时重新加载。特别地，一个 @cordisjs/group 条目的 config 是其子条目列表，因此它把更新作为子 id 上的键控 diff 应用，创建、移除或更新每个子；由于更新存活的子会重新进入这个相同的逐字段分派，组协调与条目更新一起沿树递归；

• disabled —— 设置时卸载纤维、清除时重新加载。

受管领域。核心中的隔离派生一个子上下文，在一个键处覆盖领域表 ρ（第 5.1.2 节），这在上下文树静止时足够。条目可在运行时在组之间移动，因此加载器管理自己的领域，isolate 字段按键在两种作用域规则之间选择。值 true 请求一个本地领域，对条目私有并以它的 id 打标签，条目带着它无论移动到何处；字符串请求一个全局领域，由每个命名该字符串的条目共享，因此移动这样的条目改变的是它与哪些条目共享绑定，而非它属于哪个领域。一旦没有条目命名一个领域，它即被丢弃。

重分配条目的领域取决于哪些键改变了领域、条目自身是否在已改变键处是提供者、以及要通知哪些依赖方。中间那个问题是困难的，因为一个领域符号可能被多个纤维共享，其中只有一个是提供者。加载器用定界符回答它：每个键一个符号 ρ，每个上下文在其下存储自己的标签。定界符写在上下文上并被其后代继承，因此条目的标签与提供者的恰在两者在一个 isolate 作用域内为 ρ 派生时一致，这正是 ρ 处的绑定是条目自己的且必须随它移动的情形。

Algorithm 7 Isolation realm reassignment
1 function patch_isolation(entry, $\rho'$)
2 $\rho \leftarrow$ entry ctx[@@isolate]
3 store $\leftarrow$ entry ctx[@@store]
4 $\Delta \leftarrow \{k \mid \rho(k) \neq \rho'(k)\} \triangleright$ keys whose realm changes
5 for $k$ in $\Delta$ do
6    entry ctx[$\delta_k$] $\leftarrow$ fresh tag
7    diff[k] $\leftarrow$ ($\rho(k)$, $\rho'(k)$, entry ctx[$\delta_k$], store[$\rho(k)$].fiber ctx[$\delta_k$])  
8 entry ctx[@@isolate] $\leftarrow$ $\rho'$
9 reload(entry.fiber)
10 for $k$ in $\Delta$ do

$(s_{1}, s_{2}, d_{1}, d_{2}) \leftarrow \text{diff}[k]$
if $d_{1} = d_{2}$ and store $[s_{1}]$ and not store $[s_{2}]$ then ▷ the binding is the entry's own
    store $[s_{2}] \leftarrow \text{store}[s_{1}]$
    delete store $[s_{1}]$
function affected(fiber, k)
$(s_{1}, s_{2}, d_{1}, d_{2}) \leftarrow \text{diff}[k]$
return fiber.ctx[@@isolate][k] ∈ $\{s_{1}, s_{2}\}$ and (fiber.ctx[$\delta_{k}$] = $d_{1}$) ≠ ($d_{2} = d_{1}$)
notify(entry.ctx, Δ, affected) ▷ in place of the realm test of Algorithm 3

该测试取决于定界符的一个性质。$\delta _ { k }$ 下的标签写在条目的上下文上并被从它派生的每个上下文继承，且在每次重分配时全新抽取，因此对上下文 $\gamma ^ { \prime }$

$$
\gamma^ {\prime} [ \delta_ {k} ] = d _ {1} \quad \Longleftrightarrow \quad \gamma^ {\prime} \text {is derived from the entry's context}\tag{65}
$$

把 own $( \gamma ^ { \prime } )$ 写作该条件，其中 $d _ { 2 } = d _ { 1 }$ 是其在提供者处的实例。重分配把满足 own 的上下文从 $s _ { 1 }$ 移到 $s _ { 2 }$ 而把其他留在原处，且由上面的循环，恰在提供者满足 own 时把绑定移到 $s _ { 2 }$ 。一个依赖方在其自身于 k 处的领域是绑定所在的领域时看到绑定。在 own 对依赖方和提供者一致处，两者都移动或都不移动，因此依赖方在之后看到绑定恰与之前相同。在 own 把它们分开处，一侧移动而另一侧停留，因此依赖方获得或失去绑定。不等式就是那个分离，而成员资格测试丢弃在任一领域中都不解析 k 的依赖方，移动的任何部分都够不到它们。

## 5.2.2. 热模块替换（Hot Module Replacement）

热模块替换（HMR）在模块级应用可逆效应模式：当源文件改变时（通常在开发期间），系统原地替换受影响的模块而不重启进程。由于纤维已经约束其组件的所有效应与余效应，本身是组件的模块可以仅通过纤维操作被替换：处置旧纤维恢复组件安装的一切，而从重新加载的模块实例化的新纤维重新安装它。因此 HMR 无需开发者标注的接受边界，与 Webpack [46] 或 Vite [47] 的 HMR 相反。

@cordisjs/hmr 组件提供 HMR 引擎，它分三阶段运作。

阶段 1：模块分类。引擎接受两个输入：stashed 集（内容自上次重新加载以来已改变的文件 URL）与 externals 集（不能热替换而触发完整重启的模块）。把 get\_imports(url) 写作 url 直接导入的模块，它对变化的依赖子图分类，把每个模块标记为 accepted 或 declined：

```txt
Algorithm 8 Module classification
1 function classify(stashed, externals)
2 accepted ← stashed
3 declined ← externals
4 pending ← ∅
5 for url in stashed do
```

```txt
6 | pending ← pending ∪ (get_imports(url) \ (accepted ∪ declined))
7 repeat
8 | progress ← false
9 for url in pending do
10    if get_imports(url) ∩ accepted ≠ ∅ then
11    accepted ← accepted ∪ {url}
12    pending ← pending \ {url}
13    progress ← true
14 else if get_imports(url) ⊆ declined then
15    declined ← declined ∪ {url}
16    pending ← pending \ {url}
17    progress ← true
18 else
19    pending ← pending ∪ (get_imports(url) \ (accepted ∪ declined))
20 until not progress
21 declined ← declined ∪ pending
22 return (accepted, declined)
```

以 stashed 文件的导入为种子，固定点在其一个导入被接受时接受一个模块，在其所有导入都被拒绝时拒绝它；任何未决的、被困在导入环中的模块，默认为 declined。

阶段 2：过期条目检测。使用 accepted 和 declined，引擎随后把组件条目过滤为过期的那些，即其依赖树达到一个已改变模块的条目。它用 get\_dependencies 走每个条目的树，该函数收集一个模块的传递导入并尊重 declined 作为边界：

```txt
Algorithm 9 Stale-entry detection

1 function get_dependencies(root, declined)
2    deps ← ∅
3    function traverse(url)
4    if url ∈ deps or url ∈ declined then return
5    deps ← deps ∪ {url}
6    for child in get_imports(url) do traverse(child)
7    traverse(root)
8    return deps
9 function detect(entries, accepted, declined)
10    stale_entries ← ∅
11    for entry in entries do
12    tree ← get_dependencies(entry.url, declined)
13    if tree ∩ accepted ≠ ∅ then
14    accepted ← accepted ∪ tree
15    stale_entries ← stale_entries ∪ {entry}
16    return stale_entries
```

一个条目恰在其树与 accepted 相交时过期；该树随后被折叠进 accepted，因此沿它的每个过期模块在下一阶段被失效。

阶段 3：事务性重新加载。最后，引擎重新加载过期的条目。它使 accepted 模块的缓存失效<sup>3</sup>，备份每个被移除的模块以支持回滚，然后按 url 重新导入每个过期条目的组件模块并换入一个新纤维：

```python
Algorithm 10 Transactional module reload
1 function reload(ctx, accepted, stale_entries)
2 backup ← invalidate_caches(accepted)
3 try
4    for entry in stale_entries do
5    entry.fiber.dispose()
6    entry.fiber ← ctx.use(import(entry.url), entry.config)
7 catch error
8    restore_caches(backup)
9    for entry in stale_entries do
10    entry.fiber.dispose()
11    entry.fiber ← ctx.use(backup[entry.url], entry.config)
12 throw error
```

事务性保证确保系统从不到达半重新加载状态：若任何模块导入失败（例如由于语法错误），缓存被恢复且每个过期条目从 backup[entry.url]（缓存刚被恢复的前一个组件）重建，撤销已做的交换。

## 5.3. 案例研究：Koishi（Case Study: Koishi）

Koishi 是一个构建在 Cordis 之上的开源聊天机器人应用框架<sup>4</sup>。历经四年多的开发，它积累了超过 4000 个社区贡献的插件<sup>5</sup>，从即时通讯（IM）适配器与数据库驱动到管理控制台与终端用户功能。它的规模与多样性使其成为 Cordis 动态可组合性在生产环境中的代表性验证。

元框架的表达力与通用性。Koishi 作为服务端机器人运行，其每个功能都实现为第 5.1 节上下文原语之上的一个插件；Koishi 自身只贡献聊天机器人领域的词汇。同样的模型出现在一个完全不同的运行时中：Koishi 的 Web 控制台是第二个独立的 Cordis 应用，其插件组合的是浏览器及其用户界面的原语，而非服务器的。上述迥异的设定确立了第 3 节模型的两个性质。(1) 它有表达力：其原语足以承载一个完整的生产系统，宿主框架只提供领域词汇。(2) 它通用：它固定效应与余效应如何组合，而把它们的意思留给每个应用，因此既不预设特定领域也不预设特定运行时。

无需认知开销的时间可组合性。第 1.2.1 节调查的插件系统不能在不重启扩展宿主的情况下卸载单个扩展的效应。Koishi 例行执行这个操作：编排者从控制台禁用一个插件，其效应被原地撤出；在开发期间，HMR 引擎在保存时重新应用已编辑的插件，同时保留缓存状态与系统中其他地方的活跃连接。Cordis 使这种移除不仅可能，而且对插件作者毫不费力。因为经上下文执行的效应被跟踪且其逆被自动组合（第 3.1 节），即使没有经验的作者也能为插件的上下文中介效应获得有序清理，而无需编写卸载路径。这实现了第 1.2.1 节指出的其缺失的关注点局部性：本会依赖每个作者勤勉的正确性改由抽象一次性处理。

跨开放生态的空间可组合性。与第 1.2.1 节插件系统（那里插件间依赖大体缺席）相反，Koishi 的生态呈现真实的依赖拓扑：IM 适配器提供对每个消息平台的访问，数据库驱动提供持久存储，功能插件把这些声明为余效应并访问它们。运行时重配置提供者，如切换存储后端或重连适配器，只重新激活其已解析依赖发生改变的那些依赖方（第 3.2 节）；依赖不可用的插件保持不活跃直到它出现，而不会出错。案例研究证实的正是这种组合在独立编写的代码之间成立：插件与其依赖通常由不同作者编写，他们在连接它们的余效应之外不协调任何东西，因此响应式余效应在独立贡献者的开放生态中保持装配一致。

有效性威胁。这里的证据取自单一宿主语言中的单一生态，因此不能把范式的优点与其 TypeScript 实现或 Koishi 特定领域的优点分开，而且是观察性的而非针对替代架构的受控比较。案例研究所确立的因此是存在性与采纳性结果而非量化结果；对照基线测量抽象的代价及其对开发者生产力的影响仍是未来工作。

## 6. 讨论（Discussion）

前面各节呈现的形式模型与实现为动态可组合性引入一种编程范式。本节考察该范式如何扩展到更广泛的工程关切，并讨论设计张力与开放问题。

## 6.1. 系统边界（System Boundary）

第 3.1 节中的每个效应都携带一个逆，而这个逆归结为什么由系统边界决定。边界把系统运行所针对的环境分成两部分。(1) 一个位置在边界内，当系统能够排他地修改它并恢复该修改前的状态，因此对它的一次操作被跟踪进 Γ 且可稍后恢复。(2) 一个位置在边界外，当任一能力失败，因此对它的一次操作充当 $\mathrm { i d } _ { \Gamma }$ 从而既不跟踪也不恢复。本节展开这个边界的性质及其对恢复的后果。

来自余效应的边界。一个余效应通过把一个外部位置具体化来移动边界：它把对该位置的每次访问约束到它提供的一组操作上，每个操作它都能提供一个逆，因此充当 $\mathrm { i d } _ { \Gamma }$ 的操作开始被跟踪进 Γ 并被恢复。边界因此按位置而非按媒介划定，因为前述两种能力都是位置的性质，而具体化改变的是位置如何被访问、让它的媒介保持原样。例如，当系统单独写一块内存区域时它在边界内，当其他进程也写它时在边界外；当只有系统能到达一个文件时它在边界内，如私有路径下的临时文件，当它是其他程序读写的一个路径时在边界外。移动边界本身是一种权衡，在环境是否为位置提供可逆语义与提供那些语义在每个访问上的代价之间。我们在第 6.7 节接续这暗示的协同设计。

获取与排放。触达边界之外的操作通常分两阶段进行。(1) 在获取阶段，操作获得访问并在边界内安装一条记录：open 安装一个 close 移除的描述符，malloc 保留一个 free 释放的块，fork 启动一个 kill 终止的子进程。记录本身是具体化该位置的余效应的一部分，如它所保留的一个映射中的条目，而安装该条目是一个可逆效应。该记录同时是数据可沿其离去的通道。(2) 在排放阶段，操作通过该通道推送数据，如 write 交给文件的字节或 send 放到线上的数据报，而推送充当 $\mathrm { i d } _ { \Gamma }$ ，把数据留在其他方可能读写的状态。两阶段因此落在边界相对的两侧：获取留在边界内，而排放跨越到外部。

扣留与补偿。一个仍须从排放中恢复的系统有两种可用方法。一种是把排放扣留到产生它的状态确定持久为止，即回滚恢复的输出提交问题 [48]。另一种是补偿 [49]：一个把状态恢复到应用提供的等价（比定义 33 的 ≃ 更粗）的动作，如删除被创建的文件或退还已收的费。这样的动作以与逆相同的 LIFO 顺序组合，因此第 3.1 节的组合迁移到它们。元理论不迁移：定义 60 的交换是对 ≃ 证明的，必须对照更粗的等价重新确立。

## 6.2. 服务多路复用（Service Multiplexing）

动态组件平台如 OSGi [50] 围绕服务组织组合：提供者在接口下发布、消费者绑定到它的功能单元。Cordis 余效应模型呼应这个观念，服务对应键背后的接口。提供服务的是其提供者，注入服务的是其消费者。单个服务可由多个提供者实现，而这种多重性可以两种形式实现。(1) 排他绑定：多个实现共享一个接口但一次至多一个被绑定；编排者选择哪个实现被绑定，在它们之间切换需要卸载一个提供者并加载另一个，瞬间扰动每个消费者的依赖。(2) 服务代理：一个充当接口入口的中心服务被背后的提供者和消费者都注入，使多个提供者共存且代理在它们之间分派每个请求。与排他绑定相比，代理吸收这种扰动：更新背后的提供者让代理留在原位，因此消费者对其依赖看不到变化且不触发重新加载。

服务代理支撑三种能力：负载均衡、滚动更新与跨进程调用。

负载均衡。当多个提供者共存时，代理按可配置策略（如轮询、最少负载、时延加权）或消费者命名的显式目标在它们之间分派请求。因为提供者是普通组件，它们可被添加或移除以扩大或缩小容量；每个提供者通过一个可逆效应向代理注册，因此卸载它会撤销注册并自动把它从代理的路由集丢弃。

滚动更新。运行时升级一个服务实现归结为受控的提供者转移 [51, 52]。为执行该转移，新提供者作为一个附加纤维被加载并向代理注册；一旦它变为 ACTIVE，流量逐渐从旧提供者移向新提供者（例如通过调整选择权重），而旧提供者一旦不再承载飞行中的请求即被卸载。这种提供者转移把传统上是基础设施级操作（如容器编排、蓝绿部署）的东西变成应用级组合模式。

跨进程调用。服务代理也可应用于跨进程边界 [53]。每个进程托管自己的带本地提供者的 Cordis 上下文；一个协调组件链接它们，把每个作为远程提供者对待。跨进程服务访问由保留接口的 RPC 机制中介，使分布对消费者透明。一个告诫是跨进程调用招致时延且可能飞行中失败，因此同步暴露它会阻塞调用方。打算跨进程暴露的接口因此必须对照异步契约设计。

## 6.3. 访问控制与沙箱（Access Control and Sandboxing）

给定一个由独立组件组装的应用，保护该应用需要两种互补机制：(1) 约束组件可访问哪些依赖，以及 (2) 把不可信代码与宿主环境沙箱化。Cordis 通过依赖声明与拦截支持前者；后者需要外部沙箱。

基于能力访问控制。依赖访问机制（第 5.1.4 节）已经构成对 proxy 中介属性的一种访问控制形式：组件只能访问它声明的依赖；未声明的访问引发错误。这在结构上类似于基于能力的安全 [54–56]，那里权威由持有引用而非环境权威授予。inject 声明充当能力请求，上下文 proxy 充当能力中介。由于这些请求是静态声明的，组件所需的全部 proxy 中介能力在它运行前已知，让编排者能在加载时审查与批准它们，而非在访问发生时发现。

这种中介通过拦截机制推广到细粒度策略。访问控制元数据可由上下文携带或由组件声明（定义 30），提供者在依赖被调用时查询它以决定请求是否被允许。例如，文件系统依赖可携带声明组件可读写哪些路径的元数据，提供者对照元数据检查每次调用。由于这种拦截活在上下文上而非任一方代码中，编排者可调整它以约束任何组件对依赖的访问而无需修改提供者，$\mathrm { e . g . , }$ 授予社区组件只读数据库访问而核心组件保留完全访问。再者，由于拦截只影响依赖如何被调用、不影响它是否被满足，它可以在运行时被安装、重配置或移除而不触发任何重新加载或扰动依赖图。

沙箱化不可信组件。当组件的代码不可信时，语言级访问控制不够，因为能访问宿主运行时的恶意组件可以直接触达底层对象，使这样的检查形同虚设。沙箱需要超出语言级手段可达范围的执行边界，如软件故障隔离 [57]、独立语言运行时、沙箱进程或虚拟化容器 [58]。无论何种机制，不可信组件在自己的沙箱化上下文中运行并通过桥接触达宿主提供的依赖，推广第 6.2 节的跨进程调用：同样的透明论证使这种桥接访问与本地注入不可区分。在宿主侧，桥接是一个普通纤维，其能力可被上述访问控制衰减。

## 6.4. 语言无关性与选择（Language Independence and Selection）

虽然 Cordis 用 TypeScript 实现，上下文范式是语言无关的：时空可组合性只由其两个组合维度定义，因此可在沿两者满足某些要求的任何语言中实现。我们沿每个维度依次分析这些要求。

时间可组合性。在最基本层面，时间可组合性需要闭包：可逆效应把一个动作与一个逆配对，那个逆必须作为值被捕获，连同它恢复的状态，以便能在拆卸时重放。除此之外，组件的代码与加载它的副作用必须在运行时可引入且可撤除。

语言如何满足这第二个要求取决于其执行模型。在受管运行时中，这采取程序化模块注册表的形式，其中已加载的模块可在无引用后从注册表驱逐并被垃圾回收；例如 Node.js 暴露这样的注册表。<sup>6</sup> 原生代码不暴露模块注册表，因此引入与撤除采取显式动态链接与解链的形式（如 Unix 上的 dlopen/dlclose，Windows 上的 LoadLibrary/FreeLibrary）[59]，即把目标代码加载进运行进程并稍后分离它。WebAssembly 视其嵌入者走这两条路之一：模块实例在受管嵌入者（如 JavaScript 宿主）下由宿主的回收器回收，或在原生嵌入者丢弃它时释放（如 Wasmtime）。跨这些机制，可逆效应模型把加载当作上下文上的一个效应，逆撤销模块引入的符号、类型或处理器的注册。

空间可组合性。空间可组合性需要一种让组件声明依赖、运行时提供并注入这些依赖的机制。这归结为一个依赖注入（DI）问题 [38]，它出现在跨语言不同的两个层面：依赖如何类型化，以及它们的访问如何被中介。

在类型层面，语言应提供一种让开发者表达良类型依赖访问的方式。消费者通过从其上下文读取键获得余效应，因此上下文类型（第 3.2.1 节）必须记录每个键的余效应。类型类（Haskell）[60] 与 trait（Rust）[61] 通过让提供者从其自身模块经由 instance 或 impl 扩展上下文类型实现这一点 [62]。TypeScript 的模块扩充 [63] 同样让提供者模块把声明合并进上下文类型。

在运行时层面，依赖访问必须被动态中介：键背后的余效应可能随提供者被加载与卸载而改变，且可能跨上下文不同地解析。语言因此需要一种透明地介入访问、让消费者代码不变的方式，如经 JavaScript 的 Proxy 对象 [64] 或 Python 的描述符协议 $\left( \underline { { \mathsf { q e t } } } \underline { { \mathsf { \Gamma } } } \right)$ [65]。缺少这样的原语时，运行时反射 [66, 67] 可动态中介访问，代价是类型安全与开发者体验。

跨这两个层面，元编程设施一起提供类型化与中介。注解 [68] 与装饰器把元数据附加到声明上，处理器把它展开成中介访问的访问器；编译期元编程（如 Rust 过程宏、Scala 宏 [69]、Zig comptime）为每个依赖发射一个类型化声明连同这样的访问器，省去通用拦截原语。

## 6.5. 相互依赖与组件粒度（Mutual Dependencies and Component Granularity）

在响应式余效应模型中，依赖环只是让涉及的组件永久不活跃：给定两个组件 A 和 B，若 A 需要 B 提供的键而 B 需要 A 提供的键，两者的满足谓词都不能变为真。与并发系统中的死锁（取决于调度且必须在发生时检测）不同，这个条件仅从依赖声明就可预测，因此运行时可在组件加载时报告它。

实践中，大多数看似相互的依赖可分解成消除环的更细粒度组件。考虑两个组件：服务器（提供网络接口）与访问控制器（强制授权策略）。两者双向交互：访问控制器中介到达服务器的请求，而服务器暴露修改访问控制策略的端点。整体式设计会让每个组件依赖另一个。然而，两个交互方向是逻辑上独立的关切。分解它们产生四个组件：server-core、access-control-core、request-mediation（依赖两个核心以对入站请求应用访问控制）与 policy-management（依赖两个核心以经由服务器暴露策略修改）。通过这种方法，环被消除，因为没有一个核心依赖另一个；只有集成组件依赖两者。

这种分解原则上总是可能的，因为每个双向交互可分解为独立的单向绑定，但它增加组件数量：一般情形下，给定 n 个相互交互的组件，集成组件的数量可随 n 二次增长，因为每对交互组件可能每个交互方向都需要一个独立组件。这不影响正确性或运行时性能（组件是轻量的），且更细粒度可能有益：用户获得只加载他们需要的特定集成绑定的能力，有效提高系统的可组合性。然而它可能影响开发者体验：更多组件需要更多配置、更多命名，以及理解依赖图时更多认知开销。

缓解这种粒度代价是工程关切而非理论关切。实用策略包括包打包（把相关细粒度组件分组进单个可安装单元）、基于约定的接线（自动连接名字或类型匹配模式的组件）与脚手架工具（从声明式规范生成样板集成组件）。这些策略在保持无环模型的正式保证的同时把编写负担降到更接近整体式情形。

## 6.6. 依赖类型化与版本化（Dependency Typing and Versioning）

在形式模型中，依赖链接纯粹由键同一性建立：提供键 k 的组件满足在其依赖集中声明 k 的任何组件。类型族 $\nu _ { k }$ 在单个编译单元内确保类型级一致，但当组件被独立开发与构建时这个保证瓦解，这是组件生态中的常见场景。这种瓦解导致两个不同的问题。

接口漂移。提供者可能在版本之间修改与 k 关联的接口（添加字段、改变方法签名、改变行为契约），而对照早期接口编译的消费者继续声明同一个键 k。依赖在余效应级被满足 $( k \in \mathrm { d o m } ( \sigma ) )$ ，然而运行时值不再符合消费者的期望，导致类型错误、找不到方法失败或静默行为分歧 [70]。

键冲突。两个独立开发的提供者可能用同一个键名 k 表示完全无关的接口。由于仅键同一性建立链接，期望一个提供者接口的消费者会在没有任何兼容性检查的情况下接受另一个的值。与接口漂移（提供者与消费者至少共享共同血统）不同，键冲突在期望与实际类型之间不涉及任何关系，使由此产生的失败不可预测且难以诊断。

两个问题都指向同一个缺口：余效应模型只提供名义链接（按键名）而无版本化或结构化链接（按接口兼容性）[71]。我们讨论该缺口的三种方法，从最基础设施耦合到最语言无关。

键命名空间化。把键空间从 K 扩展到 $K \times P ,$ ，其中 P 标识定义接口的包，从构造上消除键冲突：具有相同本地名的独立开发接口占据不同键。这是最直接的解法也是最耦合的：它把包命名空间嵌入形式模型本身，使系统依赖外部包注册表来键同一性。

对等依赖。更轻的耦合是通过宿主语言包管理器声明版本约束 [72]。这是 Cordis 目前采纳的方法。组件依赖在语义上是对等依赖：组件不在内部捆绑其依赖，而期望运行时上下文提供它们。带对等依赖支持的包管理器（如 npm）可强制版本兼容：若提供键的包的版本落在消费者的声明对等范围之外，不兼容在安装时被抓到，而非作为运行时失败浮现。然而，这种方法有两个局限：(1) 它依赖提供者忠实遵循语义版本化，这是不可强制执行的约定；(2) 包管理器通常把每个依赖解析到单个版本，这阻止在一个应用内加载同一包的多个版本的组件。

结构兼容性。一种完全语言无关的方法会用兼容性谓词替换成员资格检查 $k \in \mathrm { d o m } ( \sigma )$ ，该谓词验证提供者的实际接口在结构上涵盖消费者的期望。这类似于结构子类型 [73]：若提供的接口是被要求的接口的子类型，提供者满足消费者。挑战在于语言无关地定义该谓词：结构兼容性对记录类型（宽度子类型）是直接的，但对行为契约（如前置/后置条件 [74]、效应规范 [22]）变得复杂，一旦参数多态引入有界量化就不可判定 [75]。

这三种方法处理问题的不同方面。设计一个统一依赖模型，结合这些方法同时保持余效应模型的动态组合保证，仍是开放问题。

## 6.7. 与语言和操作系统的协同设计（Co-Design with Languages and Operating Systems）

第 6.4 节识别出宿主语言必须为上下文范式提供的最低要求。本节接续相反的问题，一个与该范式协同设计的语言或操作系统在该最低要求之外能提供什么。

与语言协同设计。一个围绕上下文范式设计的语言可以在两方面优于库：它赋予上下文的语义，以及它赋予效应与余效应的原语。

这样的语言可以让上下文再次隐式，同时保留第 3.3 节的上下文语义。命令式语言已让每个语句对着隐式上下文运行，而那个单一上下文既不跟踪效应也不解析余效应。上下文范式相反区分多个上下文，那里一个操作要么修改它运行所针对的上下文，要么从它派生另一个（定义 27）。原地实现修改环境上下文，正如命令式语言所做。派生实现转而引入一个独立上下文，语言必须为它提供一个构造。让上下文隐式带来人体工程学与安全两方面的好处。(1) 在库实现中，涉及效应或余效应的每个函数把上下文作为普通参数或接收者，如第 5.1 节。语言隐式提供上下文处，函数不再需要取它。(2) 每个上下文携带自己的生命周期状态与已提交视图（第 4.1 节）。库实现把上下文作为普通变量传递，因此组件可能经闭包或全局变量错误地触达另一组件的上下文。它在其中安装的效应随后泄漏出其生命周期，而它在其中读取的余效应逃出其依赖规范。让上下文隐式封上两者。

这样的语言还可以让效应与余效应为其编译器所知。(1) 对效应，一个效应迭代器（定义 51）在每一步分配一个闭包以把逆连同它恢复的状态放在一起。有了执行效应的语法，编译器可以为整个迭代发射单个状态机并把那些逆保存在其帧中。(2) 对余效应，余效应规范可被接纳进类型系统，有两个好处。第一，依赖环在编译期报告而非留给运行时（第 6.5 节）。第二，依赖可按其类型的结构而非仅键同一性比较，如行类型所做 [28]，这是第 6.6 节结构兼容性的类型级支持。

与操作系统协同设计。第 1.2.3 节观察到动态可组合性的一种粗粒度替代，那里操作系统以进程粒度提供时间可组合性，其上的容器编排器以服务粒度提供空间可组合性。与该范式协同设计的操作系统会支持细粒度组合，把组件声明的余效应规范做成它能触达的一切，并把自己的资源作为余效应提供。

这样的操作系统可以提供第 6.3 节推迟到语言外机制的那个沙箱。它通过把组件约束到它声明的依赖、在组件加载时提供它们并让它内部其余一切都不可达来实现，正如 WebAssembly 模块在实例化时从其嵌入者接收导入 [76]。它还可以把第 3.2.3 节的余效应隔离与拦截作为自己的能力提供，为每个组件不同地绑定一个键并中介它提供的访问。

这样的操作系统还可以把自己的资源作为余效应提供。边界外的资源被做成可逆的，其中运行时对照提出它的组件记录每次获取（第 6.1 节），而每个运行时保留自己的记录。把资源作为余效应提供的操作系统保留该记录一次，因为它是把资源分发出去并能把它归因于提出它的组件的一方。内存与文件描述符是直接候选，而为了恢复跟踪它们已在内核接口处完成 [77, 78]。再者，操作系统可以让第 6.1 节只能扣留或补偿的一些操作可逆。对持久存储事务性地执行写入的系统可以回滚它 [79]，而建立在写时复制或不可变存储上的系统通过移动指针到达较早状态 [80, 81]。

## 7. 相关工作（Related Work）

动态可组合性与几个成熟研究领域相交。我们调查最相关的几条工作线并把我们的贡献与每条区分开。

## 7.1. 效应与余效应系统（Effect and Coefect Systems）

第 2 节把效应与余效应作为我们工作的理论支柱做了回顾。我们先定位工业实践中常见的单子效应系统，然后调查在 Cordis 相关方向上扩展效应与余效应的三条研究线：把代数效应重铸为能力，给效应可逆语义，以及把效应与余效应统一在单一分级纪律之下。

单子效应系统。一族库把效应编码进现有通用语言的类型系统，把它们表示为运行时执行的单子值。Scala 中的 ZIO [82] 把计算建模为 ZIO[R,E,A]，TypeScript 中的 Effect-TS [83] 建模为 Effect<A,E,R>，一个其参数描述其结果、其类型化错误及其上下文必须提供的服务的泛型类型；fp-ts 库 [84] 通过基于 Reader 的单子变换器编码同样的错误与要求通道。两个特征把这些系统与 Cordis 分开。第一，跟踪是用单子嵌入买来的：程序只有写在效应类型内部才能获得它，而 Cordis 把效应作为普通宿主代码之上的一个叠加层跟踪。第二，要求由解释处理，一个提供其操作的已安装服务，而当该服务被撤出时其操作所执行的仍留在原位；Cordis 相反把每个效应与一个逆配对，并随提供者来去重新解析要求（第 3.1 节、第 3.2 节）。

作为能力的代数效应。代数效应（第 2.1 节）让效应操作对类型系统可见。离我们工作最近的扩展是 Brachthäuser 等人的 Efekt 语言，它把效应类型重新解释为能力 [85, 86]：一个效应类型表达计算从其上下文要求什么，而非它可能产生什么副作用。这个视角与我们一样把上下文当作能力的中介。Cordis 与 Efekt 有两个方面不同。(1) 在目的上，代数效应让效应可见以启用模块化解释，给一个操作许多处理程序语义，而 Cordis 让它们可见以启用跟踪与逆转，把每个上下文变换与一个逆配对。(2) 在设定上，Efekt 在类型级静态约束效应，默认基于作用域推理，其中能力是二等的并被约束在其词法作用域内，通过装箱恢复一等使用，装箱通过在类型中跟踪被捕获的能力解除该限制；Cordis 相反在运行时约束效应，旨在组件移除时完全恢复资源；第 6.7 节接续一个在此意义上让上下文成为二等的语言会提供什么。

可逆效应语义。一条平行线给效应可逆语义而非解释语义。Heunen 等人 [87] 通过把 Hughes 箭头改编为 dagger 箭头与逆箭头在可逆设定中建模副作用，捕获串行化与可变存储等操作（其操作允许逆）。这是离我们的可逆效应最近的形式化说明：两者都把每个效应与撤销它的手段配对，而非经由处理程序处理它。两者不同在于可逆性驻留何处，以及它们要求多少可逆性。Heunen 等人工作在指称的范畴设定中，那里可逆性是全局性质，因每个计算可逆而由构造保证，逆是双侧的并从范畴结构恢复。Cordis 在运行时跟踪逆并要求更少：不要求整个计算可逆，而要求每个原子效应承认单侧逆，由调用方在应用点提供而非推导，任何复合的逆随之由组合得出（第 3.1 节）。

作为统一效应与余效应的分级类型。Orchard 等人 [88] 提出分级模态类型作为涵盖效应推理（经分级单子）与余效应推理（经分级余单子）的伞形概念，在 Granule 语言中实现，证明单一类型系统可同时跟踪计算做什么与需要什么；更近的工作把余效应扩展到命令式类 Java 语言 [89, 90] 与按值调用 (call-by-push-value) [91]。所有这些都在类型级运作：效应与余效应是在词法固定作用域上于编译期检查的静态注解。我们的贡献与该分析正交：我们把同样的两个概念提升为运行时机制，这让 Cordis 能处理动态组合。时间撤除与空间依赖随已加载组件集的演化被重新解析，而非在固定程序文本上一次性敲定。

## 7.2. 编程范式（Programming Paradigms）

第 3.3.3 节把上下文范式确立为一种通过显式上下文中介效应与余效应的纪律。两个既定范式值得显式比较：一个共享我们的术语，另一个共享我们对横切关切的处理。

面向上下文编程。COP [92, 93] 为语言装备层——部分方法与类定义，它们根据执行上下文在运行时被激活与停用，使行为无需基础代码命名其上下文依赖就能适应 [94]。COP 与 Cordis 在把上下文当作一等的、运行时可变实体并动态激活与停用行为上一致，但相似是名义上的。在 COP 中，"上下文"表示环境执行情形（如位置、用户、模式），激活在动态作用域范围内改变方法分派；层既不跟踪它诱发的副作用也不逆转它们，且激活不受依赖满足约束。在 Cordis 中，上下文是中介效应与余效应的 $\Gamma _ { \infty }$ 实体：激活运行组件的可逆效应并由响应式余效应满足驱动（第 3.2 节），停用完全逆转它们。COP 变化运行什么行为；Cordis 组合并逆转组件安装什么效应与依赖。它们的差别是权衡的差别。COP 把激活折叠进宿主语言的方法分派，以语言特定性为代价获得动态作用域的层范围，而 Cordis 作为语言无关叠加层在共享上下文上响应式地解析激活。Cordis 因此只能把 COP 的全局、值驱动片段表达为余效应

——即实现之间的上下文相关选择，而非动态作用域激活。

面向方面编程。AOP [95, 96] 把横切关切模块化为一个方面：一个量化基础程序中选定连接点的切入点，以及织入每处的建议。Cordis 处理同一类会散落各组件间的上下文行为问题，但其方面对应物是余效应：许多组件声明依赖的共享中介点，因此横切行为可在那里重塑而无需编辑任何组件。两个范式随后在两个轴上不同。(1) 声明对无感：AOP 切入点是量化且无感的，匹配其代码不知其被建议的任意连接点，而 Cordis 把横切约束到每个组件声明的余效应，因此其触达恰好是那个声明表面。这带来确定性与可追踪性：应用编排者可在配置层检查并治理什么横切一个组件，而无需读取或分析其源码，而 AOP 关切只有通过量化它的方面才可读。(2) 生命周期集成：Cordis 中的横切变化由组件的效应承载，在组件卸载时被逆转并响应式传播给其依赖方，因此它是动态组合模型中的一步；动态 AOP 系统 [97, 98] 也可以在运行时织入与解织，但作为独立操作，既不绑定组件的生命周期也不在被建议代码间触发重新解析。

## 7.3. 时间可组合性（Temporal Composability）

时间可组合性关切在运行程序中替换或移除一个组件同时恢复它安装的效应。先前的方法按它们如何处理离开组件的状态与效应划分：把状态前向迁移给后继版本，通过开发者编写的清理恢复效应，在预先固定的作用域内自动逆转效应，或从运行时经介入接口累积的记录回收资源。

有状态前向迁移。一族广泛的系统无停机地替换运行程序中的组件，把它们的状态前向迁移过版本。全部遵守同一时序纪律：组件只在其到达一个安全、无交互的点之后才能被交换。Kramer 与 Magee 把该标准确立为 quiescence（静止）[51]，Vandewoude 等人后来把它放宽为扰动更小的 tranquility（安宁）[52]；我们的滚动更新模式（第 6.2 节）通过在卸载提供者之前排空飞行中的请求强制它。动态软件更新（DSU）随后经手写变换函数前向迁移状态：Hicks 等人的通用 C DSU [99]、Stoyle 等人经共自由性分析的类型安全更新点 [100] 与 Hayden 等人的 Kitsune [101] 都把旧版数据映射到新版表示，原地继承堆对象、打开的文件与连接，同时重新初始化任何未迁移的东西。同样的纪律扩展到持久状态：Overeem 等人 [102] 通过手写升级操作在保持系统可用的同时转换运行中事件存储的 schema 版本之间的数据。Erlang/OTP [15] 在进程级采取同样立场，经 code\_change/3 迁移状态并经重启受监督进程而非逆转其效应从故障恢复；JavaScript 的热模块替换（如 webpack [46]、Vite [47]）在模块级做同样的事，跨一次重新加载经 module.hot 或 import.meta.hot API 把状态交给后继。与 Cordis 的模块替换（第 5.2 节）相比，这些方法更优雅地迁移内存态：Cordis 逆转旧组件的被跟踪效应并从一个干净起点重新应用新组件的，因此组件自身的内存态在重新加载后不存活，除非放入更长命的依赖，而在可逆效应之上叠加 DSU 式前向迁移是未来工作。Cordis 的方法仍有两方面更通用：它不需要 DSU 与 HMR 所需的那种手写迁移函数，且它支持完全卸载一个组件并恢复其资源，而不仅仅原地更新一个。

开发者编写的恢复。第二族通过开发者手写的清理或补偿逻辑恢复组件的效应。插件生命周期约定（如 OSGi [50]、Eclipse 的扩展点、IntelliJ 与 VSCode）把清理委托给开发者编写的卸载回调；Command 模式 [103] 把操作连同用于撤销/重做栈的 undo 方法封装；saga 模型 [49] 把长生命周期事务结构化为每步配一个补偿动作的步骤；代数效应处理程序可以附加在拆卸时运行的终结器 [104]；事件溯源 [105] 通过追加补偿事件而非执行逆来撤销状态。在所有这些中逆是不受强制执行的义务，与操作解耦，因此被遗忘的一个静默泄漏资源（如第 1.2.1 节经验地记录）。React 的 useEffect hook [106] 最接近把效应与其逆结构上配对，返回运行时在每次重新执行前与卸载时调用的清理。其短板是可组合性：hook 只能在组件或另一个 hook 的顶层调用，绝不能在条件、循环或嵌套函数内，其效应体既不接受异步函数也不接受迭代器。效应因此不能从其他效应组装或与控制流交错，没有可据以推导复合逆的东西。Cordis 效应没有这样的限制：它们是自由组合的普通操作、可异步运行，只要求每个原子效应一个手写逆，任何复合的逆由组合推导，因此组装既有效应根本不需要写逆。这种每个效应与其逆的结构配对使完全恢复成为系统的不变量而非开发者纪律之事。

静态作用域的逆转。第三族自动逆转效应，由构造如此，但把逆转约束到预先固定的作用域。软件事务内存 [107, 108] 源自硬件事务内存 [109]，记录读写日志使一组内存操作要么提交要么中止，把内存回滚到事务前状态。可逆计算，从 Landauer 与 Bennett 的热力学分析 [110, 111] 到 Janus 等可逆语言 [112]，走得更远使整个计算的每一步全局可逆。可逆进程演算把回溯构建进语义本身：RCCS [113] 为每个进程携带一个记忆，并允许在其通向的过去因果等价时取回一步，Phillips 与 Ulidowski [114] 统一为 CCS、ACP 与 CSP 推导可逆算子同时保留它们的前向操作语义。它们的因果一致性标准是 Cordis 恢复所遵循顺序的并发对应，一个以后进先出顺序应用组件自身逆的累加器，以及第 4.3.1 节把提供者的撤出推迟到其消费者停用的守卫（定理 63）。然而触达由语义固定，所执行的每个动作保持可撤销，而 Cordis 组件为每个原子效应提供一个逆、其累加器把上下文带回其组合开始之处。线性类型 [115]、RAII [4] 与 Rust 的所有权系统 [61] 把资源的释放绑到词法区域。每个都在静态上固定逆转的作用域与触达；Cordis 相反不预先固定这样的作用域：它逆转组件生命周期上的任意上下文操作，并把词法资源管理当作互补，适合单组件内的本地资源。

介入式回收。第四族回收组件不经组件自身提供逆而获得的东西，通过在其可被运行系统控制的接口处记录其获取。Nooks [77] 包装跨 Linux 内核与其可加载扩展之间边界的每次调用，使扩展触碰的内核对象经对象跟踪器通过，其记录告诉恢复管理器在扩展失败时释放什么；shadow drivers [78] 从另一侧接入同样的调用，记录决定驱动状态的请求与配置，使重启的实例可恢复。Akeso [116] 经编译器插桩获得记录，把内核执行分成记录其状态变化与跨线程依赖的可嵌套恢复域，并把故障请求连同依赖它的每个域一起回滚。回收因此遵循运行时维护的记录而非开发者记得编写的清理，这使该族成为可逆效应的最接近的系统级先例。它与 Cordis 的差别在词汇与触达。平台固定什么可被记录，无论按内核对象类型的释放代码、按驱动类的一个 shadow 还是一个被插桩分配器的一个逆，因此组件只能持有平台已知如何释放的资源；Cordis 组件相反引入自己的效应并为每个原子效应提供一个逆（第 3.1 节）。回收同样被一次提交的请求或同一扩展的重启所界定，而 Cordis 在组件整个生命周期上逆转并把它移除传播给其依赖方，后者依次释放自己的效应（第 3.2 节）。

## 7.4. 空间可组合性（Spatial Composability）

空间可组合性关切组件的依赖如何被声明与绑定。先前机制按绑定如何响应变化划分：在初始化时接线依赖一次，响应整个组件的可用性，或以单个值的粒度传播变化。

初始化时依赖接线。两种既定机制在初始化时把组件接在一起。依赖注入框架 [38]（如 Spring [117]、Guice、Angular、Inversify）在初始化时把依赖注入组件，UI 框架上下文（如 Vue.js 的 provide/inject 与 React 的 Context API）沿组件树传递它们。一些支持动态作用域（如 Spring 的 prototype/request 作用域、Angular 的分层注入器），但两者都不响应式地重新解析：当提供者在运行时被替换或移除时，既有依赖方既不停用也不重新初始化，且没有一个提供我们组件状态机提供的那类生命周期管理。Cordis 的响应式余效应（第 3.2 节）供给这一点：通知机制在满足谓词改变时触发生命周期转移。

可用性响应式组件模型。离我们的响应式余效应最近的先例对服务可用性做出响应。OSGi 的 Declarative Services 与 iPOJO [118, 119] 让组件声明提供与要求的服务，运行时随服务出现与消失自动激活与停用它们；iPOJO 的 Gravity 项目 [119] 显式针对随服务可用性变化的自主运行时适应，其 provide/require 模型直接预示 Cordis 的 ctx.provide/ctx.get 模式。R-OSGi [53] 经 RPC 把同一抽象透明扩展到分布式设定，把网络故障映射为服务撤出事件，第 6.2 节把这一模式讨论为 Cordis 模型的扩展。所有这些系统经停用回调恢复，该回调有两个局限。第一，回调是手写的，因此资源安全取决于开发者纪律，被遗忘的一个静默泄漏。第二，回调是同步的：若拆卸需要与离开的依赖异步交换，框架不提供等待它的协议，迫使对可能已过期的引用的阻塞等待。Cordis 的响应式余效应封上两个缺口：停用逆转依赖方累积的效应，其惯性 Unloading 状态（第 4.3.3 节）在响应进一步变化前把异步拆卸运行到完成。

值级响应性。函数式响应式编程（FRP）[120] 及其现代化身（如 SolidJS 中的 signals [121, 122]、Vue 的响应式系统、Angular Signals）以值级粒度传播变化：当 signal 改变时，派生计算被同步或在调度器下重新求值 [123]。Cordis 的响应式余效应以组件级粒度运作，添加值级传播不建模的异步生命周期语义。同样的粒度差异在一致性上反向运行：在回合中、以依赖图固定的顺序传播，让 FRP 能要求没有派生计算读取更新与陈旧输入的混合，即无毛刺 (glitch freedom) [124]，而 Cordis 没有回合的对应物，编排动作一次一个到达，且只保证没有单个转移跨越其余效应的两次解析（定理 64）。两者互补而非竞争：Cordis 余效应本身可携带响应式值，组件只在其实际消费的部分上更新，把组件级响应性精化为跨两个层面的更细粒度响应式余效应。

## 8. 结论（Conclusion）



我们通过把经典效应与余效应概念提升为运行时机制，为动态可组合性呈现了一个形式基础。可逆效应处理局部时间可组合性：每个上下文变换携带一个运行时跟踪的逆，而跟踪与恢复都保持组合，因此上下文在组件移除时被恢复。响应式余效应处理局部空间可组合性：每当上下文改变时，组件对照其余效应规范被通知，每次变化被分类为激活、停用或中性，余效应隔离变化声明的键解析到什么，余效应拦截变化绑定如何使用。我们把效应上下文与余效应上下文统一进单一上下文类型，其中余效应上的一个观测等价为效应供给独立性，构成时空可组合性的编程范式。把这些机制组合进组件的概念随后给出一个动态组合演算，其元理论把时空可组合性从单个组件带到整个交错组件系统。我们把这个范式实现为 Cordis 元框架，核心库提供效应跟踪与余效应解析，以及带配置协调与热模块替换的声明式组件加载器。Koishi 案例研究在拥有超过 4000 个社区插件的生产系统中验证了 Cordis 的设计。



超越人工策划的插件生态，一个令人信服的未来验证方向是自我演化的 agent harness（第 1.2.2 节），那里 AI agent 持续且几乎无需人工监督地生成并替换自己的 harness 组件。在这种设定中应用 Cordis 会验证快速组件替换下完全恢复的时间保证，以及频繁拓扑变化下依赖协调的空间保证。这样的验证会证明该范式作为 agent harness 与其他自主系统中可恢复、协调、连续自我演化的基础的适用性。



## 参考文献（References）



[1] D. L. Parnas, “On the criteria to be used in decomposing systems into modules,” Communications of the ACM, vol. 15, no. 12, pp. 1053–1058, 1972, doi: 10.1145/361598.361623.



[2] D. Birsan, “On Plug-ins and Extensible Architectures,” ACM Queue, vol. 3, no. 2, pp. 40– 46, 2005, doi: 10.1145/1053331.1053345.



[3] B. Burns, B. Grant, D. Oppenheimer, E. Brewer, and J. Wilkes, “Borg, Omega, and Kubernetes,” Communications of the ACM, vol. 59, no. 5, pp. 50–57, 2016, doi: 10.1145/2890784.



[4] B. Stroustrup, The Design and Evolution of C++. Addison-Wesley, 1994.



[5] S. Marlow, S. Peyton Jones, A. Moran, and J. Reppy, “Asynchronous Exceptions in Haskell,” in Proceedings of the ACM SIGPLAN 2001 Conference on Programming Language Design and Implementation, in PLDI '01. New York, NY, USA: Association for Computing Machinery, 2001, pp. 274–285. doi: 10.1145/378795.378858.



[6] L. Cardelli, “Program Fragments, Linking, and Modularization,” in Proceedings of the 24th ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages (POPL 1997), ACM Press, 1997, pp. 266–277. doi: 10.1145/263699.263735.



[7] C. Szyperski, Component Software: Beyond Object-Oriented Programming, 2nd ed. Addison-Wesley, 2002.



[8] R. Lopopolo, “Harness Engineering: Leveraging Codex in an Agent-First World.” [Online]. Available: https://openai.com/index/harness-engineering/



[9] Anthropic, “Harness Design for Long-Running Application Development.” [Online]. Available: https://www.anthropic.com/engineering/harness-design-longrunning-apps



[10] L. Wang et al., “A Survey on Large Language Model Based Autonomous Agents,” Frontiers of Computer Science, vol. 18, no. 6, p. 186345, 2024, doi: 10.1007/s11704-024-40231-1.



[11] Y. Qin et al., “Tool Learning with Foundation Models,” ACM Computing Surveys, 2025, doi: 10.1145/3704435.



[12] C. Packer, V. Fang, S. G. Patil, K. Lin, S. Wooders, and J. E. Gonzalez, “MemGPT: Towards LLMs as Operating Systems,” CoRR, vol. abs/2310.08560, 2023.



[13] T. Guo et al., “Large Language Model Based Multi-Agents: A Survey of Progress and Challenges,” in Proceedings of the Thirty-Third International Joint Conference on Artificial Intelligence, in IJCAI 2024. 2024, pp. 8048–8057. doi: 10.24963/ijcai.2024/890.



[14] T. Cai, X. Wang, T. Ma, X. Chen, and D. Zhou, “Large Language Models as Tool Makers,” in Proceedings of the Twelfth International Conference on Learning Representations, in ICLR 2024. 2024. [Online]. Available: https://openreview.net/forum?id=qV83K9d5WB



[15] J. Armstrong, “Making Reliable Distributed Systems in the Presence of Software Errors,” Doctoral dissertation, 2003. [Online]. Available: https://erlang.org/download/ armstrong\_thesis\_2003.pdf



[16] E. Moggi, “Notions of computation and monads,” Information and Computation, vol. 93, no. 1, pp. 55–92, 1991, doi: 10.1016/0890-5401(91)90052-4.



[17] G. Plotkin and J. Power, “Adequacy for Algebraic Efects,” in Foundations of Software Science and Computation Structures, F. Honsell and M. Miculan, Eds., Berlin, Heidelberg: Springer Berlin Heidelberg, 2001, pp. 1–24.



[18] T. Petricek, D. Orchard, and A. Mycroft, “Coefects: unified static analysis of contextdependence,” in Proceedings of the 40th International Conference on Automata, Languages, and Programming - Volume Part II, in ICALP'13. Riga, Latvia: Springer-Verlag, 2013, pp. 385–397. doi: 10.1007/978-3-642-39212-2\_35.



[19] M. Gaboardi, S.-ya Katsumata, D. Orchard, F. Breuvart, and T. Uustalu, “Combining efects and coefects via grading,” in Proceedings of the 21st ACM SIGPLAN International Conference on Functional Programming, in ICFP 2016. Nara, Japan: Association for Computing Machinery, 2016, pp. 476–489. doi: 10.1145/2951913.2951939.



[20] A. Church, “A Formulation of the Simple Theory of Types,” The Journal of Symbolic Logic, vol. 5, no. 2, pp. 56–68, 1940, doi: 10.2307/2266170.



[21] B. C. Pierce, Types and Programming Languages. MIT Press, 2002.



[22] J. M. Lucassen and D. K. Giford, “Polymorphic Efect Systems,” in Proceedings of the 15th ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages, in POPL '88. San Diego, California, USA: Association for Computing Machinery, 1988, pp. 47–57. doi: 10.1145/73560.73564.



[23] P. Wadler, “Monads for functional programming,” in Program Design Calculi, M. Broy, Ed., Berlin, Heidelberg: Springer Berlin Heidelberg, 1993, pp. 233–264.



[24] G. Plotkin and J. Power, “Notions of Computation Determine Monads,” in Foundations of Software Science and Computation Structures, Berlin, Heidelberg: Springer Berlin Heidelberg, 2002, pp. 342–356. doi: 10.1007/3-540-45931-6\_24.



[25] G. Plotkin and M. Pretnar, “Handlers of Algebraic Efects,” in Programming Languages and Systems (ESOP), Berlin, Heidelberg: Springer Berlin Heidelberg, 2009, pp. 80–94. doi: 10.1007/978-3-642-00590-9\_7.



[26] M. Pretnar, “An Introduction to Algebraic Efects and Handlers. Invited tutorial paper,” Electron. Notes Theor. Comput. Sci., vol. 319, no. C, pp. 19–35, Dec. 2015, doi: 10.1016/ j.entcs.2015.12.003.



[27] D. Leijen, “Koka: Programming with Row Polymorphic Efect Types,” Electronic Proceedings in Theoretical Computer Science, vol. 153, pp. 100–126, Jun. 2014, doi: 10.4204/ eptcs.153.8.



[28] D. Leijen, “Type directed compilation of row-typed algebraic efects,” in Proceedings of the 44th ACM SIGPLAN Symposium on Principles of Programming Languages, in POPL '17. Paris, France: Association for Computing Machinery, 2017, pp. 486–499. doi: 10.1145/3009837.3009872.



[29] A. Bauer and M. Pretnar, “Programming with algebraic efects and handlers,” Journal of Logical and Algebraic Methods in Programming, vol. 84, no. 1, pp. 108–123, Jan. 2015, doi: 10.1016/j.jlamp.2014.02.001.



[30] K. Sivaramakrishnan et al., “Retrofitting parallelism onto OCaml,” Proc. ACM Program. Lang., vol. 4, no. ICFP, Aug. 2020, doi: 10.1145/3408995.



[31] T. Petricek, D. Orchard, and A. Mycroft, “Coefects: a calculus of context-dependent computation,” in Proceedings of the 19th ACM SIGPLAN International Conference on Functional Programming, in ICFP '14. Gothenburg, Sweden: Association for Computing Machinery, 2014, pp. 123–135. doi: 10.1145/2628136.2628160.



[32] T. Uustalu and V. Vene, “Comonadic Notions of Computation,” Electronic Notes in Theoretical Computer Science, vol. 203, no. 5, pp. 263–284, 2008, doi: 10.1016/j.entcs.2008.05.029.



[33] A. Brunel, M. Gaboardi, D. Mazza, and S. Zdancewic, “A Core Quantitative Coefect Calculus,” in Proceedings of the 23rd European Symposium on Programming Languages and Systems - Volume 8410, Berlin, Heidelberg: Springer-Verlag, 2014, pp. 351–370. doi: 10.1007/978-3-642-54833-8\_19.



[34] J. Reed and B. C. Pierce, “Distance makes the types grow stronger: a calculus for diferential privacy,” SIGPLAN Not., vol. 45, no. 9, pp. 157–168, Sep. 2010, doi: 10.1145/1932681.1863568.



[35] M. Abadi, A. Banerjee, N. Heintze, and J. G. Riecke, “A core calculus of dependency,” in Proceedings of the 26th ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages, in POPL '99. San Antonio, Texas, USA: Association for Computing Machinery, 1999, pp. 147–160. doi: 10.1145/292540.292555.



[36] D. E. Denning, “A lattice model of secure information flow,” Commun. ACM, vol. 19, no. 5, pp. 236–243, May 1976, doi: 10.1145/360051.360056.



[37] U. Dal Lago and F. Gavazzo, “A relational theory of efects and coefects,” Proc. ACM Program. Lang., vol. 6, no. POPL, Jan. 2022, doi: 10.1145/3498692.



[38] M. Fowler, “Inversion of Control Containers and the Dependency Injection pattern.” [Online]. Available: https://martinfowler.com/articles/injection.html



[39] A. M. Pitts and I. D. B. Stark, “Observable Properties of Higher Order Functions that Dynamically Create Local Names, or What's New?,” in Mathematical Foundations of Computer Science 1993 (MFCS 1993), in Lecture Notes in Computer Science, vol. 711. Springer, 1993, pp. 122–141. doi: 10.1007/3-540-57182-5\_8.



[40] G. D. Plotkin, “LCF Considered as a Programming Language,” Theoretical Computer Science, vol. 5, no. 3, pp. 223–255, 1977, doi: 10.1016/0304-3975(77)90044-5.



[41] D. R. Ghica, K. Muroya, and T. Waugh Ambridge, “A Robust Graph-Based Approach to Observational Equivalence,” Logical Methods in Computer Science, vol. 21, no. 2, p. 8:1– 8:95, 2025, doi: 10.46298/LMCS-21(2:8)2025.



[42] X. Leroy and S. Blazy, “Formal Verification of a C-like Memory Model and Its Uses for Verifying Program Transformations,” Journal of Automated Reasoning, vol. 41, no. 1, pp. 1–31, 2008, doi: 10.1007/s10817-008-9099-0.



[43] R. P. James and A. Sabry, “Yield: Mainstream Delimited Continuations,” in First International Workshop on the Theory and Practice of Delimited Continuations (TPDC 2011), 2011, pp. 20–32. [Online]. Available: https://homes.luddy.indiana.edu/sabry/files/yield.pdf



[44] A. W. Mazurkiewicz, “Trace Theory,” in Petri Nets: Central Models and Their Properties, Advances in Petri Nets 1986, Part II, in Lecture Notes in Computer Science, vol. 255. Springer, 1986, pp. 279–324. doi: 10.1007/3-540-17906-2\_30.



[45] U. A. Acar, G. E. Blelloch, and R. Harper, “Adaptive functional programming,” ACM Transactions on Programming Languages and Systems, vol. 28, no. 6, pp. 990–1034, 2006, doi: 10.1145/1186632.1186634.



[46] webpack, “Hot Module Replacement.” [Online]. Available: https://webpack.js.org/api/ hot-module-replacement



[47] Vite, “HMR API.” [Online]. Available: https://vite.dev/guide/api-hmr



[48] E. N. (M. Elnozahy, L. Alvisi, Y.-M. Wang, and D. B. Johnson, “A Survey of Rollback-Recovery Protocols in Message-Passing Systems,” ACM Computing Surveys, vol. 34, no. 3, pp. 375–408, 2002, doi: 10.1145/568522.568525.



[49] H. Garcia-Molina and K. Salem, “Sagas,” in Proceedings of the 1987 ACM SIGMOD International Conference on Management of Data, in SIGMOD '87. 1987, pp. 249–259. doi: 10.1145/38713.38742.



[50] OSGi Alliance, OSGi Core Release 8. OSGi Alliance, 2020. [Online]. Available: https:// docs.osgi.org/specification/osgi.core/8.0.0/



[51] J. Kramer and J. Magee, “The Evolving Philosophers Problem: Dynamic Change Management,” IEEE Transactions on Software Engineering, vol. 16, no. 11, pp. 1293–1306, 1990, doi: 10.1109/32.60317.



[52] Y. Vandewoude, P. Ebraert, Y. Berbers, and T. D'Hondt, “Tranquility: A Low Disruptive Alternative to Quiescence for Ensuring Safe Dynamic Updates,” IEEE Transactions on Software Engineering, vol. 33, no. 12, pp. 856–868, 2007, doi: 10.1109/tse.2007.70733.



[53] J. S. Rellermeyer, G. Alonso, and T. Roscoe, “R-OSGi: Distributed Applications Through Software Modularization,” in Proceedings of the ACM/IFIP/USENIX 8th International Middleware Conference, in Middleware '07. 2007, pp. 1–20. doi: 10.1007/978-3-540-76778-7\_1.



[54] J. B. Dennis and E. C. Van Horn, “Programming Semantics for Multiprogrammed Computations,” Communications of the ACM, vol. 9, no. 3, pp. 143–155, 1966, doi: 10.1145/365230.365252.



[55] M. S. Miller, K.-P. Yee, and J. Shapiro, “Capability Myths Demolished,” technical report SRL2003–2, 2003. [Online]. Available: http://zesty.ca/capmyths/usenix.pdf



[56] R. N. M. Watson, J. Anderson, B. Laurie, and K. Kennaway, “Capsicum: Practical Capabilities for UNIX,” in Proceedings of the 19th USENIX Security Symposium, 2010, pp. 29–46. [Online]. Available: https://www.usenix.org/legacy/events/sec10/tech/full\_papers/ Watson.pdf



[57] R. Wahbe, S. Lucco, T. E. Anderson, and S. L. Graham, “Eficient Software-Based Fault Isolation,” in Proceedings of the 14th ACM Symposium on Operating Systems Principles, in SOSP '93. 1993, pp. 203–216. doi: 10.1145/168619.168635.



[58] A. Barth, A. P. Felt, P. Saxena, and A. Boodman, “Protecting Browsers from Extension Vulnerabilities,” in Proceedings of the 17th Annual Network and Distributed System Security Symposium, in NDSS '10. 2010. [Online]. Available: https://www.ndss-symposium.org/ ndss2010/protecting-browsers-extension-vulnerabilities/



[59] W. W. Ho and R. A. Olsson, “An Approach to Genuine Dynamic Linking,” Software: Practice and Experience, vol. 21, no. 4, pp. 375–390, 1991, doi: 10.1002/SPE.4380210404.



[60] P. Wadler and S. Blott, “How to Make Ad-hoc Polymorphism Less Ad Hoc,” in Proceedings of the 16th ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages, in POPL '89. 1989, pp. 60–76. doi: 10.1145/75277.75283.



[61] N. D. Matsakis and F. S. K. II, “The Rust Language and Type System,” in ACM SIGPLAN ML Family Workshop, Gothenburg, Sweden, Sep. 2014.



[62] D. Dreyer, R. Harper, M. M. T. Chakravarty, and G. Keller, “Modular Type Classes,” in Proceedings of the 34th ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages, in POPL '07. 2007, pp. 63–70. doi: 10.1145/1190216.1190229.



[63] Microsoft, “Declaration Merging.” [Online]. Available: https://www.typescriptlang. org/docs/handbook/declaration-merging.html



[64] T. Van Cutsem and M. S. Miller, “Proxies: Design Principles for Robust Object-oriented Intercession APIs,” in Proceedings of the 6th Symposium on Dynamic Languages, in DLS '10. 2010, pp. 59–72. doi: 10.1145/1869631.1869638.



[65] R. Hettinger, “Descriptor HowTo Guide.” [Online]. Available: https://docs.python.org/ 3/howto/descriptor.html



[66] P. Maes, “Concepts and Experiments in Computational Reflection,” in Conference on Object-Oriented Programming Systems, Languages, and Applications (OOPSLA), 1987, pp. 147–155. doi: 10.1145/38765.38821.



[67] G. Bracha and D. M. Ungar, “Mirrors: design principles for meta-level facilities of objectoriented programming languages,” in Proceedings of the 19th Annual ACM SIGPLAN Conference on Object-Oriented Programming, Systems, Languages, and Applications (OOP-SLA), 2004, pp. 331–344. doi: 10.1145/1028976.1029004.



[68] R. Rouvoy and P. Merle, “Leveraging component-based software engineering with Fraclet,” Annals of Telecommunications, vol. 64, no. 1–2, pp. 65–79, 2009, doi: 10.1007/ s12243-008-0072-z.



[69] E. Burmako, “Scala Macros: Let Our Powers Combine!,” in Proceedings of the 4th Workshop on Scala, in SCALA@ECOOP '13. 2013, p. 3:1–3:10. doi: 10.1145/2489837.2489840.



[70] S. Raemaekers, A. van Deursen, and J. Visser, “Semantic Versioning and Impact of Breaking Changes in the Maven Repository,” Journal of Systems and Software, vol. 129, pp. 140–158, 2017, doi: 10.1016/j.jss.2016.04.008.



[71] P. Lam, J. Dietrich, and D. J. Pearce, “Putting the Semantics into Semantic Versioning,” in Proceedings of the 2020 ACM SIGPLAN International Symposium on New Ideas, New Paradigms, and Reflections on Programming and Software, in Onward! '20. 2020, pp. 157– 179. doi: 10.1145/3426428.3426922.



[72] P. Abate, R. Di Cosmo, R. Treinen, and S. Zacchiroli, “Dependency Solving: A Separate Concern in Component Evolution Management,” Journal of Systems and Software, vol. 85, no. 10, pp. 2228–2240, 2012, doi: 10.1016/j.jss.2012.02.018.



[73] L. Cardelli, “Structural Subtyping and the Notion of Power Type,” in Proceedings of the 15th ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages, in POPL '88. 1988, pp. 70–79. doi: 10.1145/73560.73566.



[74] B. Meyer, “Applying "Design by Contract",” Computer, vol. 25, no. 10, pp. 40–51, 1992, doi: 10.1109/2.161279.



[75] B. C. Pierce, “Bounded Quantification is Undecidable,” Information and Computation, vol. 112, no. 1, pp. 131–165, 1994, doi: 10.1006/inco.1994.1055.



[76] A. Haas et al., “Bringing the web up to speed with WebAssembly,” in Proceedings of the 38th ACM SIGPLAN Conference on Programming Language Design and Implementation (PLDI), ACM, 2017, pp. 185–200. doi: 10.1145/3062341.3062363.



[77] M. M. Swift, B. N. Bershad, and H. M. Levy, “Improving the reliability of commodity operating systems,” in Proceedings of the 19th ACM Symposium on Operating Systems Principles (SOSP), ACM, 2003, pp. 207–222. doi: 10.1145/945445.945466.



[78] M. M. Swift, M. Annamalai, B. N. Bershad, and H. M. Levy, “Recovering device drivers,” ACM Transactions on Computer Systems, vol. 24, no. 4, pp. 333–360, 2006, doi: 10.1145/1189256.1189257.



[79] D. E. Porter, O. S. Hofmann, C. J. Rossbach, A. Benn, and E. Witchel, “Operating System Transactions,” in Proceedings of the 22nd ACM Symposium on Operating Systems Principles (SOSP), ACM, 2009, pp. 161–176. doi: 10.1145/1629575.1629591.



[80] O. Kiselyov and C.-chieh Shan, “Delimited Continuations in Operating Systems,” in Modeling and Using Context (CONTEXT 2007), in Lecture Notes in Computer Science, vol. 4635. Springer, 2007, pp. 291–302. doi: 10.1007/978-3-540-74255-5\_22.



[81] E. Dolstra and A. Löh, “NixOS: a purely functional Linux distribution,” in Proceedings of the 13th ACM SIGPLAN International Conference on Functional Programming (ICFP), ACM, 2008, pp. 367–378. doi: 10.1145/1411204.1411255.



[82] ZIO, “ZIO: Type-safe, composable asynchronous and concurrent programming for Scala.” [Online]. Available: https://zio.dev/



[83] Efect, “Efect: A TypeScript library for building robust applications.” [Online]. Available: https://efect.website/



[84] G. Canti, “fp-ts: Functional programming in TypeScript.” [Online]. Available: https:// github.com/gcanti/fp-ts



[85] J. I. Brachthäuser, P. Schuster, and K. Ostermann, “Efects as capabilities: efect handlers and lightweight efect polymorphism,” Proc. ACM Program. Lang., vol. 4, no. OOPSLA, 2020, doi: 10.1145/3428194.



[86] J. I. Brachthäuser, P. Schuster, E. Lee, and A. Boruch-Gruszecki, “Efects, capabilities, and boxes: from scope-based reasoning to type-based reasoning and back,” Proc. ACM Program. Lang., vol. 6, no. OOPSLA1, 2022, doi: 10.1145/3527320.



[87] C. Heunen, R. Kaarsgaard, and M. Karvonen, “Reversible Efects as Inverse Arrows,” in Proceedings of the Thirty-Fourth Conference on the Mathematical Foundations of Programming Semantics (MFPS XXXIV), in Electronic Notes in Theoretical Computer Science, vol. 341. 2018, pp. 179–199. doi: 10.1016/j.entcs.2018.11.009.



[88] D. Orchard, V.-B. Liepelt, and H. Eades III, “Quantitative program reasoning with graded modal types,” Proc. ACM Program. Lang., vol. 3, no. ICFP, 2019, doi: 10.1145/3341714.



[89] R. Bianchini, F. Dagnino, P. Giannini, E. Zucca, and M. Servetto, “Coefects for sharing and mutation,” Proc. ACM Program. Lang., vol. 6, no. OOPSLA2, Oct. 2022, doi: 10.1145/3563319.



[90] R. Bianchini, F. Dagnino, P. Giannini, and E. Zucca, “A Java-like calculus with heterogeneous coefects,” Theoretical Computer Science, vol. 971, p. 114063, 2023, doi: https://doi. org/10.1016/j.tcs.2023.114063.



[91] C. Torczon, E. Suárez Acevedo, S. Agrawal, J. Velez-Ginorio, and S. Weirich, “Efects and Coefects in Call-by-Push-Value,” Proc. ACM Program. Lang., vol. 8, no. OOPSLA2, Oct. 2024, doi: 10.1145/3689750.



[92] R. Hirschfeld, P. Costanza, and O. Nierstrasz, “Context-oriented Programming,” Journal of Object Technology, vol. 7, no. 3, pp. 125–151, 2008, doi: 10.5381/jot.2008.7.3.a4.



[93] P. Costanza and R. Hirschfeld, “Language constructs for context-oriented programming: an overview of ContextL,” in Proceedings of the 2005 Symposium on Dynamic Languages (DLS '05), ACM, 2005, pp. 1–10. doi: 10.1145/1146841.1146842.



[94] G. Salvaneschi, C. Ghezzi, and M. Pradella, “Context-oriented programming: A software engineering perspective,” Journal of Systems and Software, vol. 85, no. 8, pp. 1801–1817, 2012, doi: 10.1016/j.jss.2012.03.024.



[95] G. Kiczales et al., “Aspect-Oriented Programming,” in ECOOP'97 — Object-Oriented Programming, 11th European Conference, in Lecture Notes in Computer Science, vol. 1241. Springer, 1997, pp. 220–242. doi: 10.1007/BFb0053381.



[96] G. Kiczales, E. Hilsdale, J. Hugunin, M. Kersten, J. Palm, and W. G. Griswold, “An Overview of AspectJ,” in ECOOP 2001 — Object-Oriented Programming, 15th European Conference, in Lecture Notes in Computer Science, vol. 2072. Springer, 2001, pp. 327–353. doi: 10.1007/3-540-45337-7\_18.



[97] A. Popovici, T. Gross, and G. Alonso, “Dynamic Weaving for Aspect-Oriented Programming,” in Proceedings of the 1st International Conference on Aspect-Oriented Software Development (AOSD 2002), ACM, 2002, pp. 141–147. doi: 10.1145/508386.508404.



[98] J. Bonér, “What Are the Key Issues for Commercial AOP Use: How Does AspectWerkz Address Them?,” in Proceedings of the 3rd International Conference on Aspect-Oriented Software Development (AOSD 2004), ACM, 2004, pp. 5–6. doi: 10.1145/976270.976273.



[99] M. Hicks, J. T. Moore, and S. Nettles, “Dynamic Software Updating,” in Proceedings of the ACM SIGPLAN 2001 Conference on Programming Language Design and Implementation, in PLDI '01. 2001, pp. 13–23. doi: 10.1145/378795.378798.



[100] G. Stoyle, M. Hicks, G. Bierman, P. Sewell, and I. Neamtiu, “Mutatis Mutandis: Safe and Predictable Dynamic Software Updating,” in Proceedings of the 32nd ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages, in POPL '05. 2005, pp. 183– 194. doi: 10.1145/1040305.1040321.



[101] C. M. Hayden, K. Saur, E. K. Smith, and M. Hicks, “Kitsune: Eficient, General-Purpose Dynamic Software Updating for C,” ACM Trans. Program. Lang. Syst., vol. 36, no. 4, 2014, doi: 10.1145/2629460.



[102] M. Overeem, M. Spoor, and S. Jansen, “The Dark Side of Event Sourcing: Managing Data Conversion,” in IEEE 24th International Conference on Software Analysis, Evolution and Reengineering, in SANER '17. 2017, pp. 193–204. doi: 10.1109/SANER.2017.7884621.



[103] E. Gamma, R. Helm, R. Johnson, and J. Vlissides, Design Patterns: Elements of Reusable Object-Oriented Software. Boston, MA: Addison-Wesley, 1994.



[104] D. Leijen, “Algebraic Efect Handlers with Resources and Deep Finalization,” technical report MSR-TR-2018-10, Apr. 2018. [Online]. Available: https://www.microsoft.com/ en-us/research/publication/algebraic-efect-handlers-resources-deep-finalization/



[105] M. Fowler, “Event Sourcing.” 2005.



[106] J. Lee, J. Ahn, and K. Yi, “React-tRace: A Semantics for Understanding React Hooks,” Proc. ACM Program. Lang., vol. 9, no. OOPSLA2, pp. 471–498, 2025, doi: 10.1145/3763067.



[107] N. Shavit and D. Touitou, “Software Transactional Memory,” in Proceedings of the Fourteenth Annual ACM Symposium on Principles of Distributed Computing, in PODC '95. 1995, pp. 204–213. doi: 10.1145/224964.224987.



[108] T. Harris, S. Marlow, S. Peyton Jones, and M. Herlihy, “Composable Memory Transactions,” in Proceedings of the Tenth ACM SIGPLAN Symposium on Principles and Practice of Parallel Programming, in PPoPP '05. 2005, pp. 48–60. doi: 10.1145/1065944.1065952.



[109] M. Herlihy and J. E. B. Moss, “Transactional Memory: Architectural Support for Lock-Free Data Structures,” in Proceedings of the 20th Annual International Symposium on Computer Architecture, in ISCA '93. 1993, pp. 289–300. doi: 10.1145/165123.165164.



[110] R. Landauer, “Irreversibility and Heat Generation in the Computing Process,” IBM Journal of Research and Development, vol. 5, no. 3, pp. 183–191, 1961, doi: 10.1147/rd.53.0183.



[111] C. H. Bennett, “Logical Reversibility of Computation,” IBM Journal of Research and Development, vol. 17, no. 6, pp. 525–532, 1973, doi: 10.1147/rd.176.0525.



[112] T. Yokoyama and R. Glück, “A Reversible Programming Language and its Invertible Self-Interpreter,” in Proceedings of the 2007 ACM SIGPLAN Workshop on Partial Evaluation and Semantics-Based Program Manipulation, in PEPM '07. 2007, pp. 144–153. doi: 10.1145/1244381.1244404.



[113] V. Danos and J. Krivine, “Reversible Communicating Systems,” in CONCUR 2004 — Concurrency Theory, 15th International Conference, in Lecture Notes in Computer Science, vol. 3170. Springer, 2004, pp. 292–307. doi: 10.1007/978-3-540-28644-8\_19.



[114] I. Phillips and I. Ulidowski, “Reversing Algebraic Process Calculi,” in Foundations of Software Science and Computation Structures, 9th International Conference (FOSSACS 2006), in Lecture Notes in Computer Science, vol. 3921. Springer, 2006, pp. 246–260. doi: 10.1007/11690634\_17.



[115] P. Wadler, “Linear Types Can Change the World!,” in Programming Concepts and Methods: Proceedings of the IFIP Working Group 2.2/2.3 Working Conference, North-Holland, 1990, pp. 561–581. [Online]. Available: https://homepages.inf.ed.ac.uk/wadler/papers/ linear/linear.ps



[116] A. Lenharth, V. S. Adve, and S. T. King, “Recovery domains: an organizing principle for recoverable operating systems,” in Proceedings of the 14th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS), ACM, 2009, pp. 49–60. doi: 10.1145/1508244.1508251.



[117] C. Walls, Spring in Action, 6th ed. Manning Publications, 2022. [Online]. Available: https://www.manning.com/books/spring-in-action-sixth-edition



[118] C. Escofier, R. S. Hall, and P. Lalanda, “iPOJO: an Extensible Service-Oriented Component Framework,” in IEEE International Conference on Services Computing, 2007, pp. 474– 481. doi: 10.1109/SCC.2007.74.



[119] H. Cervantes and R. S. Hall, “Autonomous Adaptation to Dynamic Availability Using a Service-Oriented Component Model,” in Proceedings of the 26th International Conference on Software Engineering, in ICSE '04. 2004, pp. 614–623. doi: 10.1109/ICSE.2004.1317483.



[120] C. Elliott and P. Hudak, “Functional Reactive Animation,” in Proceedings of the Second ACM SIGPLAN International Conference on Functional Programming, in ICFP '97. 1997, pp. 263–273. doi: 10.1145/258948.258973.



[121] G. H. Cooper and S. Krishnamurthi, “Embedding Dynamic Dataflow in a Call-by-Value Language,” in Programming Languages and Systems (ESOP 2006), in Lecture Notes in Computer Science, vol. 3924. Springer, 2006, pp. 294–308. doi: 10.1007/11693024\_20.



[122] I. Maier and M. Odersky, “Deprecating the Observer Pattern with Scala.React,” technical report EPFL-REPORT-176887, 2012. [Online]. Available: https://infoscience.epfl.ch/ record/176887



[123] E. Bainomugisha, A. L. Carreton, T. Van Cutsem, W. De Meuter, and others, “A Survey on Reactive Programming,” ACM Comput. Surv., vol. 45, no. 4, 2013, doi: 10.1145/2501654.2501666.



[124] A. Margara and G. Salvaneschi, “On the Semantics of Distributed Reactive Programming: The Cost of Consistency,” IEEE Trans. Software Eng., vol. 44, no. 7, pp. 689–711, 2018, doi: 10.1109/TSE.2018.2833109.













