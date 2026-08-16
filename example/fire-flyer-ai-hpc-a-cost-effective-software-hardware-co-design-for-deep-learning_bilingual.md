<!-- 中英对照版：左英文、右中文，逐段对齐 -->

# Fire-Flyer AI-HPC：一种面向深度学习的高性价比软硬件协同设计

| 英文 | 中文 |
|------|------|
| Wei An, Xiao Bi, Guanting Chen, Shanhuang Chen,Chengqi Deng, Honghui Ding, Kai Dong, Qiushi Du, Wenjun Gao, Kang Guan, Jianzhong Guo, Yongqiang Guo, Zhe Fu, Ying He, Panpan Huang, Jiashi Li, Wenjun Gao, Kang Guan, Jianzhong Guo, Yongqiang Guo, Zhe Fu, Ying He, Panpan Huang, Jiashi Li, | Wei An, Xiao Bi, Guanting Chen, Shanhuang Chen, Chengqi Deng, Honghui Ding, Kai Dong, Qiushi Du, Wenjun Gao, Kang Guan, Jianzhong Guo, Yongqiang Guo, Zhe Fu, Ying He, Panpan Huang, Jiashi Li, |

| 英文 | 中文 |
|------|------|
| Wenfeng Liang, Xiaodong Liu, Xin Liu, Yiyuan Liu, Yuxuan Liu, Shanghao Lu, Xuan Lu, Xiaotao Nie,    Tian Pei, Junjie Qiu, Hui Qu, Zehui Ren, Zhangli Sha, Xuecheng Su, Xiaowen Sun, Yixuan Tan, Minghui Tang,    Shiyu Wang, Yaohui Wang, Yongji Wang, Ziwei Xie, Yiliang Xiong, Yanhong Xu, Shengfeng Ye, Shuiping Yu,    Yukun Zha, Liyue Zhang\*, Haowei Zhang, Mingchuan Zhang, Wentao Zhang, Yichao Zhang, Chenggang Zhao, Yao Zhao, Shangyan Zhou, Shunfeng Zhou, Yuheng Zou | Wenfeng Liang, Xiaodong Liu, Xin Liu, Yiyuan Liu, Yuxuan Liu, Shanghao Lu, Xuan Lu, Xiaotao Nie, Tian Pei, Junjie Qiu, Hui Qu, Zehui Ren, Zhangli Sha, Xuecheng Su, Xiaowen Sun, Yixuan Tan, Minghui Tang, Shiyu Wang, Yaohui Wang, Yongji Wang, Ziwei Xie, Yiliang Xiong, Yanhong Xu, Shengfeng Ye, Shuiping Yu, Yukun Zha, Liyue Zhang\*, Haowei Zhang, Mingchuan Zhang, Wentao Zhang, Yichao Zhang, Chenggang Zhao, Yao Zhao, Shangyan Zhou, Shunfeng Zhou, Yuheng Zou |

| 英文 | 中文 |
|------|------|
| DeepSeek-AI, Beijing, China | DeepSeek-AI, Beijing, China |

| 英文 | 中文 |
|------|------|
| research@deepseek.com | research@deepseek.com |

| 英文 | 中文 |
|------|------|
| Abstract—The rapid progress in Deep Learning (DL) and Large Language Models (LLMs) has exponentially increased demands of computational power and bandwidth. This, combined with the high costs of faster computing chips and interconnects, has significantly inflated High Performance Computing (HPC) construction costs. To address these challenges, we introduce the Fire-Flyer AI-HPC architecture, a synergistic hardware-software co-design framework and its best practices. For DL training, we deployed the Fire-Flyer 2 with 10,000 PCIe A100 GPUs, achieved performance approximating the DGX-A100 while reducing costs by half and energy consumption by 40%. We specifically engineered HFReduce to accelerate allreduce communication and implemented numerous measures to keep our Computation-Storage Integrated Network congestion-free. Through our software stack, including HaiScale, 3FS, and HAI-Platform, we achieved substantial scalability by overlapping computation and communication. Our system-oriented experience from DL training provides valuable insights to drive future advancements in AI-HPC. | 摘要——深度学习（Deep Learning, DL）和大语言模型（Large Language Model, LLM）的迅猛发展，使对算力与带宽的需求呈指数级增长。加之更快的计算芯片与互联成本高昂，高性能计算（High Performance Computing, HPC）的建设成本被显著推高。为应对这些挑战，我们提出了 Fire-Flyer AI-HPC 架构，一套软硬件协同设计框架及其最佳实践。在深度学习训练方面，我们部署了包含 10,000 块 PCIe A100 GPU 的 Fire-Flyer 2，其性能逼近 DGX-A100，同时成本降低一半、能耗降低 40%。我们专门设计了 HFReduce 来加速 allreduce 通信，并采取了众多措施保证我们的计算存储一体化网络（Computation-Storage Integrated Network）无拥塞。通过我们的软件栈，包括 HaiScale、3FS 和 HAI-Platform，我们以计算与通信重叠的方式实现了可观的扩展性。我们在深度学习训练中积累的面向系统的经验，为驱动 AI-HPC 的未来进步提供了宝贵洞见。 |

| 英文 | 中文 |
|------|------|
| Index Terms—High Performance Computing, Cost-Effective, All-Reduce, Best Practices, Deep Learning, Machine Learning, Large Language Models, Artificial Intelligence Infrastructure | 索引词——高性能计算、高性价比、全归约、最佳实践、深度学习、机器学习、大语言模型、人工智能基础设施 |

## I. 引言

| 英文 | 中文 |
|------|------|
| In recent years, Deep Learning (DL) [1] has developed rapidly and is widely used in image recognition, speech recognition, content generation, autonomous driving, and other areas. The rapid development of DL is fundamentally tied to the support rendered by data. Training with copious amounts of data demands massive computational resources. Relying on Moore's Law [2], computer speeds double every two years on average, but the pace of DL far exceeds this speed. In particular, Large Language Models (LLMs) [3]–[7] that have become popular in recent years have exploded the demand for computational resources and memory. The parameters of LLMs can reach tens to thousands of billions, requiring hundreds or thousands of GPUs for training. Although LLM training is challenging, the emerging capabilities resulting from more parameters have shown the benefits of continued model expansion. Since then, researchers have gone down the path of making models bigger and never looked back. To acquire more computational resources, people have to expand more nodes. This leads to a surge in the cost of building AI infrastructure. How to reduce the cost of new data centers and how to build cost-effective clusters are also hot and challenging problems. Moreover, more nodes lead to higher energy consumption, which contradicts this era's goal of reducing carbon emissions and achieving carbon neutrality. Reducing energy consumption is also a challenging problem. | 近年来，深度学习（DL）[1] 发展迅速，被广泛应用于图像识别、语音识别、内容生成、自动驾驶等领域。深度学习的快速发展根本上依赖于数据所提供的支撑。用海量数据训练模型需要庞大的计算资源。依托摩尔定律 [2]，计算机速度平均每两年翻一番，但深度学习的发展速度远超于此。特别是近年来流行的大语言模型（LLM）[3]–[7]，更是引爆了计算资源与内存的需求。LLM 的参数规模可达数百亿乃至数千亿，训练需要成百上千块 GPU。尽管 LLM 训练极具挑战，但更多参数所涌现出的新能力已经证明了持续扩大模型的好处。自此，研究者们在把模型做得更大的道路上一去不复返。为了获取更多计算资源，人们不得不扩展更多节点，这导致 AI 基础设施的建设成本激增。如何降低新建数据中心的开销、如何构建高性价比的集群，都是热门且充满挑战的问题。此外，节点越多能耗越高，这与本时代减少碳排放、实现碳中和的目标相悖。降低能耗同样是一个富有挑战的问题。 |

| 英文 | 中文 |
|------|------|
| In this paper, leverage our practical experience accumulated over the years to propose cost-effective strategies cost-effective strategies for constructing AI-HPC systems suitable for deep learning and LLMs. | 在本文中，我们利用多年积累的实践经验，提出了构建适用于深度学习和 LLM 的高性价比 AI-HPC 系统的策略。 |

| 英文 | 中文 |
|------|------|
| Fire-Flyer AI-HPC Architecture: We have deployed a cluster composed of 10,000 PCIe A100 GPUs for Deep Learning training purposes. Details about the GPU nodes and network topology are provided in Section III-A, where we compare our architecture to the NVIDIA DGX-A100 [8] in terms of cost-effectiveness and lower CO2 emissions. In contrast, we must invest more in software optimizations to address the performance challenges of the PCIe architecture. The following sections will discuss about software-hardware co-design. | Fire-Flyer AI-HPC 架构：我们部署了一个由 10,000 块 PCIe A100 GPU 组成的集群用于深度学习训练。GPU 节点与网络拓扑的细节见第三节-A，我们在那里将我们的架构与 NVIDIA DGX-A100 [8] 在性价比与更低的 CO2 排放方面进行了对比。与之相对，我们必须投入更多软件优化来应对 PCIe 架构的性能挑战。以下各节将讨论软硬件协同设计。 |

## 我们架构中的关键技术主题（Key Technical Topics in our Architecture）

| 英文 | 中文 |
|------|------|
| • Network Co-Design: The Two-Layer Fat-Tree Network [9] integrates storage and computation network, as shown in Section III-B. The entire network is divided into two zones, and the platform supports cross-zone tasks. To prevent congestion, we employed various network tunings detailed in Section VI-A. | • 网络协同设计：两层胖树网络 [9] 将存储网络与计算网络一体化，见第三节-B。整个网络被划分为两个区域，平台支持跨区域任务。为防止拥塞，我们采用了第六节-A 中详述的多种网络调优手段。 |

| 英文 | 中文 |
|------|------|
| • HFReduce: Achieves computation-communication overlap via asynchronous allreduce on the CPU, outperforming NVIDIA Collective Communications Library (NCCL) [10] on our PCIe architecture, as discussed in Section IV. | • HFReduce：通过 CPU 上的异步 allreduce 实现计算与通信重叠，在我们的 PCIe 架构上性能优于 NVIDIA 集合通信库（NCCL）[10]，详见第四节。 |

| 英文 | 中文 |
|------|------|
| • HaiScale: As described in Section V, optimizes parallelism methods for our PCIe architecture, such as Data Parallelism (DP), Pipeline Parallelism (PP) [11] [12], Tensor Parallelism (TP) [13] [14], Experts Parallelism (EP) [15]–[17], Fully Sharded Data Parallel(FSDP) [18] and Zero Redundancy Optimizer(ZeRO) [19]. | • HaiScale：如第五节所述，针对我们的 PCIe 架构优化并行方式，如数据并行（Data Parallelism, DP）、流水线并行（Pipeline Parallelism, PP）[11] [12]、张量并行（Tensor Parallelism, TP）[13] [14]、专家并行（Experts Parallelism, EP）[15]–[17]、全分片数据并行（Fully Sharded Data Parallel, FSDP）[18] 与零冗余优化器（Zero Redundancy Optimizer, ZeRO）[19]。 |

| 英文 | 中文 |
|------|------|
| • 3FS Distributed File System: Addresses I/O bottlenecks in big data AI tasks, configures with our communication and network tuning, reduces congestion in storage and computation integrated network topology, as detailed in Section VI-B. | • 3FS 分布式文件系统：解决大数据 AI 任务中的 I/O 瓶颈，配合我们的通信与网络调优，减少存储与计算一体化网络拓扑中的拥塞，详见第六节-B。 |

| 英文 | 中文 |
|------|------|
| • HAI Platform [20]: Offers task scheduling, fault handling, and disaster recovery, enhancing utilization and reducing costs. It provides an open-box solution for deep-learning researchers. It is already open-sourced: https://github.com/HFAiLab/hai-platform | • HAI Platform [20]：提供任务调度、故障处理与容灾恢复，提高利用率、降低成本，为深度学习研究者提供开箱即用的解决方案。现已开源：https://github.com/HFAiLab/hai-platform |

| 英文 | 中文 |
|------|------|
| Stability and Robustness: These are crucial topics in HPC. Our systems are equipped with robust mechanisms to handle hardware failures, minimizing downtime and impact on operations. These mechanisms, discussed in Section VII, include: | 稳定性与鲁棒性：这些是 HPC 中的关键主题。我们的系统配备了稳健的机制来应对硬件故障，将停机时间及其对运行的影响降至最低。这些机制在第七节中讨论，包括： |

| 英文 | 中文 |
|------|------|
| • Disaster recovery through our checkpoint manager | • 通过我们的检查点管理器实现容灾恢复 |

| 英文 | 中文 |
|------|------|
| • A validator utility for detecting hardware failures | • 用于检测硬件故障的校验器工具 |

| 英文 | 中文 |
|------|------|
| • An overview of real hardware failure data from our cluster over the past year. | • 我们集群过去一年真实硬件故障数据的概览。 |

| 英文 | 中文 |
|------|------|
| We hope these insights will be beneficial to industry peers and researchers alike. | 我们希望这些见解能对业界同行和研究者有所助益。 |

| 英文 | 中文 |
|------|------|
| Discussion and Future Work: In Section VIII, we address some common questions regarding PCIe architecture, such as congestion control, maintenance cost, and stability compared with other architectures. In Section IX, we propose the next generation of PCIe architecture, which is aimed at Mixture-of-Experts Large Language Models training and primarily utilizes multi-NICs and a Multi-Plane network. | 讨论与未来工作：在第八节中，我们讨论关于 PCIe 架构的一些常见问题，如拥塞控制、维护成本，以及与其他架构相比的稳定性。在第九节中，我们提出下一代 PCIe 架构，该架构面向混合专家大语言模型训练，主要采用多网卡与多平面网络。 |

## II. 背景

## A. 深度学习的演进

| 英文 | 中文 |
|------|------|
| The revolution in Machine Learning and Deep Learning began in 2012 with AlexNet [21], which outperformed traditional methods in image classification, marking the onset of big data utilization and increased computational demands. The emergence of ResNet [22], with its deeper layers, further broadened the horizons of image processing, truly bringing about the “deep" in “"Deep Learning". At the same time, big datadriven model training nudged the evolution of data storage technology, leading to the advent of all-flash SSD distributed file systems. | 机器学习与深度学习的革命始于 2012 年的 AlexNet [21]，它在图像分类上超越了传统方法，标志着大数据利用时代的开启以及计算需求的增长。层数更深的 ResNet [22] 的出现，进一步拓宽了图像处理的视野，真正带来了"深度学习"中的"深度"。与此同时，大数据驱动的模型训练推动了数据存储技术的演进，催生了全闪存 SSD 分布式文件系统。 |

| 英文 | 中文 |
|------|------|
| Fast forward to 2017, Google's Transformer [23] made its grand entry, introducing the concept of "Attention is all you need", shaking up the field of Natural Language Processing (NLP). With the advent of more complex models like AlphaFold [24] and AlphaZero [25] highlighting the need for more computational power and memory, revealing the limitations of traditional FP64 / FP32 computing devices. | 时间来到 2017 年，谷歌的 Transformer [23] 隆重登场，提出了"注意力就是一切"（Attention is all you need）的概念，撼动了自然语言处理（Natural Language Processing, NLP）领域。随着 AlphaFold [24] 和 AlphaZero [25] 等更复杂模型的出现，人们对计算能力和内存的需求愈发突出，传统 FP64/FP32 计算设备的局限性也暴露无遗。 |

| 英文 | 中文 |
|------|------|
| Entering the 2020s saw the rise of LLMs as a game-changer in the AI sector. Research indicates that an upscale in the number of language model parameters and computational budget can significantly enhance model performance, given adequate training data. Consequently, despite requiring colossal computational resources, efforts are being made to train large models on tens or hundreds of billions or even trillions of parameters. Pioneering examples include GPT-3 [26] and PaLM [27], which occupy close to 1TB of GPU Memory. Recognizing the potential, industry giants have set up large AI clusters to train LLMs while constantly investing in computational power chips. | 进入 2020 年代，LLM 的崛起成为 AI 领域的游戏规则改变者。研究表明，在训练数据充足的前提下，增加语言模型的参数量和计算预算可显著提升模型性能。因此，尽管需要庞大的计算资源，业界仍在努力训练参数规模达数百亿、数千亿甚至数万亿的大模型。开创性的例子包括 GPT-3 [26] 和 PaLM [27]，它们占用近 1TB 的 GPU 内存。认识到这一潜力后，行业巨头纷纷搭建大型 AI 集群来训练 LLM，同时持续投入算力芯片。 |

| 英文 | 中文 |
|------|------|
| ![](images/64ab5abd3e6749ffd287b64f210843a09a0d12b7072221968f39614311c3ab83.jpg)   Figure 1: The Exponential Growth of Computational Power for Deep Learning. | ![](images/64ab5abd3e6749ffd287b64f210843a09a0d12b7072221968f39614311c3ab83.jpg) 图 1：深度学习计算能力的指数级增长。 |

| 英文 | 中文 |
|------|------|
| The shift towards the Mixture-of-Experts (MoE) Models [28]–[30] architecture starting from GPT-4 [7], and the recent AI Generated Content (AIGC) multi-modal (Sora [31]) has amplified the demand for memory and computational resources. However, as AI development outpaces hardware development, leading to skyrocketing training costs, adopting cost-saving solutions has become imperative. | 从 GPT-4 [7] 开始转向混合专家（Mixture-of-Experts, MoE）模型 [28]–[30] 架构，以及近期 AI 生成内容（AIGC）多模态（Sora [31]）的兴起，进一步放大了对内存和计算资源的需求。然而，随着 AI 发展速度超过硬件发展速度，导致训练成本飞涨，采用节省成本的解决方案已势在必行。 |

| 英文 | 中文 |
|------|------|
| Figure 1 illustrates the exponential growth of computational power for DL. And as summarized in Figure 2 [32], while AI's demand for computational power is growing at 10x per year, Moore's Law lags behind with hardware FLOPs increase at only 3.0x every two years, DRAM bandwidth at 1.6x, and interconnect bandwidth at 1.4x. This disparity necessitates more machines, raising DL training costs, particularly for LLM training, where the computational power required surpasses that of traditional HPC applications. | 图 1 展示了深度学习计算能力的指数级增长。如图 2 [32] 所总结的，AI 对计算能力的需求以每年 10 倍的速度增长，而摩尔定律却明显滞后：硬件算力每两年仅增长 3.0 倍，DRAM 带宽仅增长 1.6 倍，互联带宽仅增长 1.4 倍。这种差距迫使人们部署更多机器，推高了深度学习训练成本，尤其是 LLM 训练——其所需算力已超过传统 HPC 应用。 |

## B. 模型训练中的挑战与对策

| 英文 | 中文 |
|------|------|
| In Deep Learning training, a single task demands hundreds of GPUs and consumes substantial storage and network resources. This massive scale introduces system-level challenges: | 在深度学习训练中，单个任务就需要数百块 GPU，并消耗大量的存储与网络资源。这种规模带来了系统层面的挑战： |

| 英文 | 中文 |
|------|------|
| 1) Efficiency: Firstly, achieving efficient training at this magnitude is crucial. Model FLOPs Utilization (MFU), which assesses the ratio of observed throughput to theoretical maximum throughput (assuming 100% peak FLOPS), serves as the standard metric for evaluating training efficiency. Training LLMs involves dividing models among GPUs that communicate extensively for progress. Besides communication, factors like operation optimization, data pre-processing, and GPU memory consumption significantly influence MFU. Multiple parallel strategies are employed to enhance efficiency: | 1) 效率：首先，在如此规模下实现高效训练至关重要。模型算力利用率（Model FLOPs Utilization, MFU）用于评估观测吞吐量与理论最大吞吐量（假设 100% 峰值算力）之比，是评估训练效率的标准指标。训练 LLM 需要在 GPU 之间切分模型，而这些 GPU 之间要频繁通信以推进训练。除通信外，算子优化、数据预处理、GPU 内存占用等因素也显著影响 MFU。人们采用多种并行策略来提升效率： |

| 英文 | 中文 |
|------|------|
| ![](images/ac736950c2194cc6b10238e6acb2c195754581dcceea90f15a85e84771636121.jpg)   Figure 2: Scaling of Peak Hardware FLOPS, and Memory/Interconnect Bandwidth. | ![](images/ac736950c2194cc6b10238e6acb2c195754581dcceea90f15a85e84771636121.jpg) 图 2：峰值硬件算力及内存/互联带宽的扩展趋势。 |

| 英文 | 中文 |
|------|------|
| • Data Parallelism (DP): Models and optimizer states are replicated across multiple devices with data evenly distributed to all. For LLMs training, the Zero Redundancy Optimizer (ZeRO) [19] further enhances this method by sharding these states on each data parallel process and using allgather and reduce-scatter for parameter fetching and gradient calculation. | • 数据并行（DP）：模型与优化器状态在多个设备上复制，数据均匀地分配给所有设备。对于 LLM 训练，零冗余优化器（ZeRO）[19] 通过在各个数据并行进程上分片这些状态，并利用全收集（allgather）与归约散播（reduce-scatter）来获取参数和计算梯度，进一步增强了该方法。 |

| 英文 | 中文 |
|------|------|
| • Pipeline Parallelism (PP): Each device holds a portion of the model layers with each training batch divided into micro-batches for pipeline execution. Efficient scheduling strategies like GPipe [11], PipeDream 1F1B [12], and Zero Bubble Pipeline Parallelism (ZBPP) [33], are required to minimize “pipeline bubbles". | • 流水线并行（PP）：每个设备持有模型层的一部分，每个训练批次被划分为微批次进行流水线执行。需要 GPipe [11]、PipeDream 1F1B [12] 和零气泡流水线并行（ZBPP）[33] 等高效调度策略，以最大限度减少"流水线气泡"。 |

| 英文 | 中文 |
|------|------|
| • Tensor Parallelism (TP): This involves placing a model layer on multiple GPUs that perform computations in parallel [13] [14]. It includes row-wise and column-wise parallelism, necessitating allgather and all2all for input splitting and output merging. | • 张量并行（TP）：将一个模型层放置在多个 GPU 上并行计算 [13] [14]，包括行并行与列并行，需要通过全收集和全对全（all2all）实现输入切分与输出合并。 |

| 英文 | 中文 |
|------|------|
| • Expert Parallelism (EP): MoE Models’ different expert models are distributed on different GPUs during MoE training [15]–[17]. The gate model selects tokens for allocation during input, with corresponding tokens sent to experts model via all2all communication. | • 专家并行（EP）：MoE 模型的不同专家模型在 MoE 训练期间被分布到不同 GPU 上 [15]–[17]。门控模型（gate model）在输入时选择词元（token）进行分配，对应的 token 通过全对全通信发送到各专家模型。 |

| 英文 | 中文 |
|------|------|
| • Fully Sharded Data Parallel (FSDP) is an implementation based on the ZeRO Stage 3 algorithm [19]. FSDP partitions the model's parameters, optimizer states, and gradients, distributing them across different GPUs, with each GPU retaining only 1/n of the total. During forward propagation, FSDP performs an allgather operation to assemble the complete parameters, which are then released after the forward pass is completed. Similarly, during backward propagation, FSDP conducts an allgather operation to obtain the complete parameters, followed by backward computation to calculate gradients. It then performs a reduce-scatter operation to synchronize gradients across all GPUs, resulting in each GPU holding 1/n of the reduced gradients. Finally, FSDP updates the 1/n parameters using each GPU’s 1/n gradients and optimizer states. FSDP reduces GPU memory usage by maintaining only 1/n of the parameters, gradients, and optimizer states on each GPU, enabling training of largerscale models. | • 全分片数据并行（FSDP）是基于 ZeRO Stage 3 算法 [19] 的一种实现。FSDP 将模型的参数、优化器状态和梯度分区，分布到不同 GPU 上，每块 GPU 仅保留总量的 1/n。前向传播时，FSDP 执行一次全收集操作组装完整参数，前向完成后即释放。类似地，反向传播时 FSDP 执行全收集获取完整参数，随后反向计算梯度；再执行归约散播在所有 GPU 间同步梯度，使每块 GPU 持有归约后梯度的 1/n。最后，FSDP 用每块 GPU 的 1/n 梯度与优化器状态更新其持有的 1/n 参数。由于每块 GPU 只维护 1/n 的参数、梯度与优化器状态，FSDP 显著降低了 GPU 内存占用，从而可以训练更大规模的模型。 |

| 英文 | 中文 |
|------|------|
| There are additional strategies and algorithms to accelerate training or reduce memory usage, such as Activation Recomputation [34], [35], as well as enhanced communication and computation overlap during parallelism [36], among others. | 此外还有加速训练或减少内存占用的其他策略与算法，如激活重计算（Activation Recomputation）[34]、[35]，以及在并行过程中增强通信与计算重叠 [36] 等。 |

| 英文 | 中文 |
|------|------|
| 2) Stability: The second challenge is achieving highstability training at scale, i.e., maintaining efficient training throughout the process. Stability is vital from a production standpoint as training a big model with a trillion tokens may span several weeks. In DL training, stragglers and hardware failures are common occurrences rather than outliers. Stragglers can decelerate tasks involving hundreds of GPUs, emphasizing the importance of stability and task recovery time. | 2) 稳定性：第二个挑战是实现在规模下的高稳定训练，即在训练全程保持高效运行。从生产角度看，稳定性至关重要，因为用一万亿个词元训练一个大模型可能持续数周。在深度学习训练中，掉队者（straggler）和硬件故障是常态而非个例。掉队者会拖慢涉及数百块 GPU 的任务，凸显了稳定性与任务恢复时间的重要性。 |

## C. 这一时代的 HPC 与 AI 集群（C. HPC and AI Clusters of This Era）

| 英文 | 中文 |
|------|------|
| 1) HPC Inadequacies for AI Training: Traditional supercomputers such as TianHe-2A [37], Stampede 2 [38], and Sunway TaihuLight [39] primarily focus on double precision calculations and do not support the FP16 precision, rendering them unsuitable for DL training. Fugaku [40], despite its high performance, does not support tensor GEMM acceleration, a key component for DL workloads. Although these supercomputers may not be well-suited for DL training, their robust high-performance networks and extensive experience in largescale cluster construction offer valuable insights and lessons for subsequent researchers. | 1) HPC 之于 AI 训练的不足：天河二号 [37]、Stampede 2 [38]、神威·太湖之光 [39] 等传统超级计算机主要面向双精度计算，不支持 FP16 精度，无法胜任深度学习训练。富岳（Fugaku）[40] 尽管性能强大，却不支持张量 GEMM 加速——这是深度学习负载的关键组件。虽然这些超级计算机可能并不适合深度学习训练，但它们稳健的高性能网络以及在大规模集群建设方面的丰富经验，为后来的研究者提供了宝贵洞见与经验。 |

| 英文 | 中文 |
|------|------|
| 2) GPU based HPC: Supercomputers like Frontier [41], Aurora [42], Summit [43] and Perlmutter [44] utilize highperformance GPUs to tackle large-scale computations. It's worth mentioning that Perlmutter utilizes an all-flash storage system, achieving a peak bandwidth of 5TB/s. Indeed, conducting DL training on these GPU-based HPCs yields significant performance. | 2) 基于 GPU 的 HPC：Frontier [41]、Aurora [42]、Summit [43] 和 Perlmutter [44] 等超级计算机利用高性能 GPU 处理大规模计算。值得一提的是，Perlmutter 采用全闪存存储系统，峰值带宽达 5TB/s。确实，在这些基于 GPU 的 HPC 上进行深度学习训练能取得显著性能。 |

| 英文 | 中文 |
|------|------|
| 3) GPU Clusters of Large Companies: Meta, formerly Facebook, has developed its AI-HPC using a softwarehardware co-design approach, with one system utilizing IB and another employing RoCE [45], [46]. ByteDance initially implemented a DL cluster with a mix of CPU and PCIe GPU [47]. However, with the advent of the LLMs era, they adopted an architecture similar to DGX, building a cluster with over 10,000 GPUs [48]. Alibaba has developed its own HPN network [49] for LLMs training using NVIDIA H800 GPUs. NVIDIA also has its own AI-HPC Eos [50], which will feature 576 DGX H100 systems totaling 4,608 H100 GPUs. While this will provide a considerable boost in computational power for AI tasks, the high cost of DGX systems raises questions about economic viability. | 3) 大公司的 GPU 集群：Meta（原 Facebook）采用软硬件协同设计的方法构建了自己的 AI-HPC，一套系统采用 IB，另一套采用 RoCE [45]、[46]。字节跳动最初采用 CPU 与 PCIe GPU 混合的深度学习集群 [47]，但随着 LLM 时代的到来，他们采用了类似 DGX 的架构，构建了拥有超过 10,000 块 GPU 的集群 [48]。阿里巴巴利用 NVIDIA H800 GPU 开发了自己的 HPN 网络 [49] 用于 LLM 训练。NVIDIA 也有自己的 AI-HPC Eos [50]，将包含 576 套 DGX H100 系统，共计 4,608 块 H100 GPU。虽然这将为 AI 任务带来可观的算力提升，但 DGX 系统的高昂成本也引发了经济性方面的疑问。 |

| 英文 | 中文 |
|------|------|
| 4) AI DSA Clusters: Custom-designed AI DSA (Domain Specific Architecture) accelerators like Google's TPU [51] , utilize highly advanced optical switch reconfigurable networks. Alternatives to traditional GPU setups, like Intel Habana Gaudi [52], are also available. Teslahas introduced the Dojo [53], [54] supercomputer , which uses System on | 4) AI DSA 集群：定制设计的 AI DSA（领域专用架构）加速器，如谷歌的 TPU [51]，采用高度先进的光交换可重构网络。传统 GPU 方案之外的替代品，如 Intel Habana Gaudi [52]，也同样可用。特斯拉推出了 Dojo [53]、[54] 超级计算机，它使用晶圆级（System on Wafer）技术将整片硅晶圆做成单个芯片。 |

| 英文 | 中文 |
|------|------|
| ![](images/03fcda2dbc85760f46c83dafeceda0f53f65b0eb56adafbf1911d45683adc851.jpg)   Figure 3: Size of Model Parameter and Accelerator Memory | ![](images/03fcda2dbc85760f46c83dafeceda0f53f65b0eb56adafbf1911d45683adc851.jpg) 图 3：模型参数量与加速器内存规模。 |

| 英文 | 中文 |
|------|------|
| Wafer technology to build an entire silicon wafer as a single chip. Huawei has designed the Ascend AI DSA chip [55], [56], which remains competitive with NVIDIA, as noted by NVIDIA CEO Jensen Huang. These accelerators are tailored for efficient execution of AI workloads, offering specialized features to optimize model training and inference. However their software ecosystems, while progressing, still require further development to match the maturity of NVIDIA's offerings. | 华为设计了昇腾（Ascend）AI DSA 芯片 [55]、[56]，按 NVIDIA 首席执行官黄仁勋的说法，它依然与 NVIDIA 保持竞争力。这些加速器专为高效执行 AI 负载而定制，提供面向模型训练与推理优化的专用特性。然而它们的软件生态虽然在不断进步，要达到 NVIDIA 方案的成熟度仍需进一步发展。 |

| 英文 | 中文 |
|------|------|
| 5) Cloud Service Providers: Cloud service providers, such as Azure, offer flexible and scalable resources for AI training. Despite their convenience and easy accessibility, the costs can accumulate significantly over time. For long-term projects spanning around two years, these costs could amount to purchasing an entire dedicated cluster. Therefore, this option may not be the most economical choice for extensive AI computations. | 5) 云服务提供商：Azure 等云服务商为 AI 训练提供灵活可扩展的资源。尽管方便易用，但成本会随时间显著累积。对于约两年期的长期项目，这些成本可能足以购买一个完整的专用集群。因此，对于大规模 AI 计算而言，这一选项未必是最经济的。 |

## D. AI 基础设施面临的挑战（D. Challenges in AI Infrastructure）

| 英文 | 中文 |
|------|------|
| As models continue to grow larger, DL training requires thousands of GPUs. Additionally, researchers often need to train multiple models simultaneously. Therefore, a cluster with at least tens of thousands of GPUs can meet the needs of AI practitioners. In addition to increasing the scale of the cluster nodes and adding more GPUs, there's also a need to find ways to save on the overall system construction costs. These costs include but are not limited to power support, cooling, networking, storage, fault handling, disaster recovery, etc. Building a cost-effective AI-HPC system is a significant challenge. The question of how to construct a high-performance, efficient, economical, and environmentally friendly HPC to meet AI training requirements has become a hot topic. Some works, such as [57] analyzes the construction of HPC, discussed the interconnection of heterogeneous clusters, cooling systems. AI applications such as Peng Cheng Cloud Brain II [58] discussed their strategies for building and improving AI computing power and cluster communication efficiency, which helped them achieve first place in IO500 and AIPerf rankings. | 随着模型不断变大，深度学习训练需要数千块 GPU。此外，研究者往往需要同时训练多个模型。因此，至少拥有数万块 GPU 的集群才能满足 AI 从业者的需求。除了扩大集群节点规模、增加更多 GPU 之外，还需要设法节省系统整体建设成本。这些成本包括但不限于供电、散热、网络、存储、故障处理、容灾恢复等。构建高性价比的 AI-HPC 系统是一个重大挑战。如何构建高性能、高效、经济且环保的 HPC 以满足 AI 训练需求，已成为热门话题。一些工作，如 [57] 分析了 HPC 的建设，讨论了异构集群的互联与散热系统。鹏城云脑 II [58] 等 AI 应用介绍了他们建设与提升 AI 算力、集群通信效率的策略，帮助他们取得了 IO500 和 AIPerf 排名第一。 |

| 英文 | 中文 |
|------|------|
| Drawing from our extensive experience in Deep Learning spanning over the past decade, we have conducted considerable exploration in terms of cost-effectiveness. This work primarily discusses our practices for achieving cost-effectiveness and high-performance across different models and stages. | 基于我们过去十余年的深度学习丰富经验，我们在成本效益方面进行了大量探索。本工作主要讨论我们如何在不同的模型与阶段实现高性价比与高性能。 |

| 英文 | 中文 |
|------|------|
| ![](images/450c5640fe3dbc309a11ed1f73b9719180542900ee3ff6d3f1068c535f27d95d.jpg)   Figure 4: In-node Architecture: 8 PCIe GPUs and 1 Infini-Band (IB) NIC are directly connected to the CPU. Note that GPU5/6 share the same PCIe root port, while IB occupies one independently. | ![](images/450c5640fe3dbc309a11ed1f73b9719180542900ee3ff6d3f1068c535f27d95d.jpg) 图 4：节点内部架构：8 块 PCIe GPU 与 1 块 InfiniBand (IB) 网卡直接连接到 CPU。注意 GPU5/6 共享同一 PCIe 根端口，而 IB 网卡独占一个。 |

| 英文 | 中文 |
|------|------|
| Table I: Our Arch and DGX-A100 Server Hardware Details | 表 I：我们的架构与 DGX-A100 服务器的硬件细节 |

**英文表**

|  | Our PCIe Arch | DGX-A100 |
| --- | --- | --- |
| CPU | 2 * AMD 32 CoresEPYC Rome/Milan CPU | 2 * AMD 64 CoresEPYC 7742 CPU |
| Memory | 512GB 16-ChannelsDDR4-3200Mhz | 2048GB 16-ChannelsDDR4-3200Mhz |
| GPU | 8*PCIe-A100-40GB | 8*SXM-A100-40GB |
| NICs | 1 * Mellanox InfiniBandcx6 200Gbps NIC | 9 * Mellanox InfiniBandcx6 200Gbps NIC |
| NVLINK | 600 GB/s between eachpair of GPUs | 600 GB/s interconnectamong all 8 GPUs |

**中文表**

| | 我们的 PCIe 架构 | DGX-A100 |
|---|---|---|
| CPU | 2 \* AMD 32 核 EPYC Rome/Milan CPU | 2 \* AMD 64 核 EPYC 7742 CPU |
| 内存 | 512GB 16 通道 DDR4-3200Mhz | 2048GB 16 通道 DDR4-3200Mhz |
| GPU | 8 \* PCIe-A100-40GB | 8 \* SXM-A100-40GB |
| 网卡 | 1 \* Mellanox InfiniBand CX6 200Gbps 网卡 | 9 \* Mellanox InfiniBand CX6 200Gbps 网卡 |
| NVLINK | 每对 GPU 之间 600 GB/s | 全部 8 块 GPU 之间 600 GB/s 互联 |

## III. 萤火二号（FIRE-FLYER 2）：我们用于深度学习和早期 LLM 训练的方案（III. FIRE-FLYER 2: OUR APPROACH FOR DEEP LEARNING AND EARLY LLM TRAINING）

| 英文 | 中文 |
|------|------|
| As mentioned in the Background Section, LLMs generally require significant memory resources. In contrast, many other models necessitate considerably less memory, as illustrated in Figure 3. Popular models like ResNet [22], Mask-RCNN [59], BERT [60], MAE [61], among others, all have a parameter volume less than 1B, signifying relatively low memory requirements. Therefore, when designing a cluster primarily for deep learning model training, and with insights gleaned from our Fire-Flyer 1 experiments, we deemed it prudent to incorporate PCIe A100 GPUs, which proved to be sufficient during its construction in 2021. | 如背景部分所述，LLM 通常需要庞大的内存资源。相比之下，许多其他模型所需内存要少得多，如图 3 所示。ResNet [22]、Mask-RCNN [59]、BERT [60]、MAE [61] 等流行模型的参数量均小于 10 亿，意味着内存需求相对较低。因此，在设计一个主要用于深度学习模型训练的集群时，并结合我们从萤火一号（Fire-Flyer 1）实验中获得的经验，我们认为采用 PCIe A100 GPU 是明智之选——在 2021 年建设时它已被证明是够用的。 |

## A. 萤火二号：PCIe A100 GPU 架构（A. Fire-Flyer 2: PCIe A100 GPU Architecture）

| 英文 | 中文 |
|------|------|
| In our training workloads, the bandwidth requirements for both storage IOs and computation communication across 8 NVIDIA PCIe A100 GPUs can be met by a single 200Gbps NVIDIA Mellanox ConnectX-6 (CX6) InfiniBand (IB) NIC. We employed the following computation node architecture , as shown in Figure 4: | 在我们的训练负载中，跨 8 块 NVIDIA PCIe A100 GPU 的存储 I/O 与计算通信带宽需求，可由一块 200Gbps 的 NVIDIA Mellanox ConnectX-6 (CX6) InfiniBand (IB) 网卡满足。我们采用了如下计算节点架构，如图 4 所示： |

| 英文 | 中文 |
|------|------|
| • 8 NVIDIA A100 PCIe GPUs and 1 Mellanox CX6 200Gbps IB NIC: directly connect to the CPU, without using a PCIe switch | • 8 块 NVIDIA A100 PCIe GPU 和 1 块 Mellanox CX6 200Gbps IB 网卡：直接连接到 CPU，不使用 PCIe 交换机 |

| 英文 | 中文 |
|------|------|
| • IB NIC occupies a separate PCIe root complex, thus avoiding performance interference with the GPU. | • IB 网卡独占一个独立的 PCIe 根复合体，从而避免与 GPU 的性能相互干扰。 |

| 英文 | 中文 |
|------|------|
| • Reserved the possibility of NVLink Bridge addition in design: As expected, when the LLM era arrived, we indeed added an NVLink Bridge between PCIe cards. | • 设计上保留了加装 NVLink 桥（NVLink Bridge）的可能：如预期那样，当 LLM 时代到来时，我们确实在 PCIe 卡之间加装了 NVLink 桥。 |

| 英文 | 中文 |
|------|------|
| Table I shows our arch details and compared with NVIDIA standard DGX-A100 server. | 表 I 展示了我们的架构细节，并与 NVIDIA 标准 DGX-A100 服务器进行了对比。 |

## B. 网络拓扑：存储与计算一体化的两层胖树

| 英文 | 中文 |
|------|------|
| We selected the Fat-Tree [9] topology as our primary network architecture due to its exceptionally high bisection bandwidth, making it the preferred choice for AI-HPC and highthroughput storage environments. Although the Dragonfly topology [62], [63] also offers comparable cost-effectiveness and performance, its lack of sufficient bisection bandwidth makes it unsuitable for our integrated storage and computation network design. At the time of implementation, various RoCE (RDMA over Converged Ethernet) [64] technologies were not as mature as they are today, so we opted for InfiniBand (IB) as our network solution. Mellanox QM8700 InfiniBand Switch, offering 40 ports at 200 Gbps, was utilized. Our cluster, consisting of 10,000 A100 GPUs, includes approximately 1,250 GPU compute nodes and nearly 200 storage servers, although a Two-Layer Fat-Tree can accommodate up to 800 nodes (configured with 20 spine switches and 40 leaf switches). | 我们选择胖树 [9] 拓扑作为主要网络架构，因为它具有极高的对分带宽，是 AI-HPC 与高吞吐存储环境的首选。尽管 Dragonfly 拓扑 [62]、[63] 也能提供相当的性价比与性能，但其对分带宽不足，不适合我们存储与计算一体化的网络设计。在实施时，各种 RoCE（融合以太网上的 RDMA）[64] 技术尚不如今天成熟，因此我们选择了 InfiniBand (IB) 作为网络方案。我们采用了 Mellanox QM8700 InfiniBand 交换机，提供 40 个 200Gbps 端口。我们的集群由 10,000 块 A100 GPU 组成，包括约 1,250 个 GPU 计算节点和近 200 台存储服务器，而两层胖树最多可容纳 800 个节点（配置 20 台脊交换机与 40 台叶交换机）。 |

| 英文 | 中文 |
|------|------|
| To reduce costs, , we opted for a two-zone network configuration instead of a three-layer Fat-Tree solution, as shown in Figure 5. Each zone consists of an 800-port Fat-Tree connected to approximately 600 GPU compute nodes. Each storage server equipped with two IB NICs, respectively connected to different zones, hence all GPU compute nodes could share a set of storage services. Additionally, the two zones are interconnected with a limited number of links. Our HAI Platform scheduling strategy ensured that cross-zone computing tasks were limited to one at most. Whether using NCCL [10] or our in-house developed communication library HFReduce, it can be run across zones by using a double binary tree algorithm [65]. Our scheduler ensures that in this topology, only one pair of nodes communicates across zones. Consequently, even tasks requiring all nodes can efficiently run on the entire Fire-Flyer 2 AI-HPC. | 为降低成本，我们选择了双区域（two-zone）网络配置，而非三层胖树方案，如图 5 所示。每个区域由一个 800 端口的胖树组成，连接约 600 个 GPU 计算节点。每台存储服务器配备两块 IB 网卡，分别连接到不同的区域，因此所有 GPU 计算节点都能共享一套存储服务。此外，两个区域之间用有限数量的链路互联。我们的 HAI 平台调度策略确保跨区域计算任务最多只有一个。无论是使用 NCCL [10] 还是我们自研的通信库 HFReduce，都可以通过双二叉树算法 [65] 跨区域运行。我们的调度器保证在这种拓扑下，只有一对节点跨区域通信。因此，即便是需要全部节点的任务，也能在整台 Fire-Flyer 2 AI-HPC 上高效运行。 |

| 英文 | 中文 |
|------|------|
| ![](images/bc3a3be1d1a6f8819bdf892127b2ee0bb489f579cc131a7fa3c6ddbb68765422.jpg)   Figure 5: Network Topology: Two complete Two-Layer Fat-Tree connected together. | ![](images/bc3a3be1d1a6f8819bdf892127b2ee0bb489f579cc131a7fa3c6ddbb68765422.jpg) 图 5：网络拓扑：两棵完整的两层胖树连接在一起。 |

| 英文 | 中文 |
|------|------|
| Table II: A100 PCIe Compared to DGX-A100. | 表 II：A100 PCIe 与 DGX-A100 的对比。 |

**英文表**

|  | Our Arch | DGX Arch |
| --- | --- | --- |
| TF32 GEMM (TFLOPS/GPU) | 107 | 131 |
| FP16 GEMM (TFLOPS/GPU) | 220 | 263 |
| Relative Performance | 83% | 100% |
| Node Relative Price | 60% | 100% |
| Cost-Performance Ratio | 1.38 | 1 |
| Power Consumption (Watts) | 2500 | 4200 |

**中文表**

| | 我们的架构 | DGX 架构 |
|---|---|---|
| TF32 GEMM (TFLOPS/GPU) | 107 | 131 |
| FP16 GEMM (TFLOPS/GPU) | 220 | 263 |
| 相对性能 | 83% | 100% |
| 节点相对价格 | 60% | 100% |
| 性价比 | 1.38 | 1 |
| 功耗（瓦） | 2500 | 4200 |

| 英文 | 中文 |
|------|------|
| Table III: Relative Cost Comparison. | 表 III：相对成本对比。 |

**英文表**

|  | OurArch | PCIe Arch withThree Layer Fat-Tree | DGXArch |
| --- | --- | --- | --- |
| Number of Switches | 122 | 200 | 1320 |
| Network Price | 350 | 600 | 4000 |
| Server Price | 11250 | 11250 | 19000 |
| Total Price | 11600 | 11850 | 23000 |

**中文表**

| | 我们的架构 | 三层胖树的 PCIe 架构 | DGX 架构 |
|---|---|---|---|
| 交换机数量 | 122 | 200 | 1320 |
| 网络价格 | 350 | 600 | 4000 |
| 服务器价格 | 11250 | 11250 | 19000 |
| 总价 | 11600 | 11850 | 23000 |

## C. 我们架构的成本性能

| 英文 | 中文 |
|------|------|
| Compared to the NVIDIA DGX-A100 [8] architecture, our approach using PCIe A100 achieves approximately 83% of the performance in TF32 and FP16 General Matrix Multiply (GEMM) benchmarks. However, it offers substantial reductions in both costs and energy usage, achieving 60% of the GPU cost and energy consumption, as detailed in Table II. | 与 NVIDIA DGX-A100 [8] 架构相比，我们采用 PCIe A100 的方案在 TF32 和 FP16 通用矩阵乘法（GEMM）基准上达到约 83% 的性能，但成本和能耗都大幅降低，实现了 60% 的 GPU 成本与能耗，详见表 II。 |

| 英文 | 中文 |
|------|------|
| Contrasting with the DGX-A100 cluster, which necessitates a Three-Layer Fat-Tree encompassing 10,000 access points and involving 320 core switches, 500 spine switches and 500 leaf switches, amounting to 1,320 switches in total (as shown in Table III), our architecture only requires 122 switches. This arrangement is significantly more cost-efficient. Even when compared to a similarly sized three-layer Fat-Tree network with 1,600 access points, which includes 40 core switches and 160 spine and leaf switches (totaling 200 switches), our design facilitates a saving of 40% in networking costs. | 与需要三层胖树的 DGX-A100 集群相比——后者需覆盖 10,000 个接入点，涉及 320 台核心交换机、500 台脊交换机和 500 台叶交换机，共 1,320 台交换机（如表 III 所示）——我们的架构只需要 122 台交换机。这在成本上要高效得多。即使与规模相近的三层胖树网络（1,600 个接入点，含 40 台核心交换机与 160 台脊/叶交换机，共 200 台交换机）相比，我们的设计也节省了 40% 的网络成本。 |

| 英文 | 中文 |
|------|------|
| Furthermore, by utilizing an 800-Ports Frame Switch, we have further reduced the cost of optical modules and cables. While there is a performance gap due to the inherent differences between PCIe card specifications and SXM, we generally achieved 80% of the DGX-A100 performance at merely 60% of the cost. Additionally, we managed to trim energy consumption by 40%, thereby reducing CO2 emissions. In terms of cost-performance, we regard this approach as both effective and successful. | 此外，通过使用 800 端口框式交换机，我们进一步降低了光模块与线缆的成本。尽管由于 PCIe 卡与 SXM 在规格上的固有差异存在性能差距，我们通常仍能仅以 60% 的成本实现 DGX-A100 80% 的性能。此外，我们成功削减了 40% 的能耗，从而减少了 CO2 排放。就性价比而言，我们认为这一方案既有效又成功。 |

## IV. HFREDUCE：网络中的软硬件协同设计

| 英文 | 中文 |
|------|------|
| In large-scale deep learning training, allreduce is essential for aggregating gradients across GPUs. To optimize communication among PCIe GPUs in our architecture, we developed HFReduce, a library specifically designed for efficient allreduce operations. The core strategy of HFReduce, illustrated in Figure 6, involves performing intra-node reduction first, followed by inter-node allreduce of the reduced data from the 8 | 在大规模深度学习训练中，allreduce 对于在 GPU 之间聚合梯度至关重要。为了优化我们架构中 PCIe GPU 之间的通信，我们开发了 HFReduce——一个专为高效 allreduce 操作设计的库。如图 6 所示，HFReduce 的核心策略是：先在节点内进行归约，然后对 8 块 GPU 归约后的数据进行跨节点 allreduce。 |

| 英文 | 中文 |
|------|------|
| ![](images/c0cdec69772c879b11c6dc8df5f84972f3f198146af3508df3ca47472992f12d.jpg)   Figure 6: HFReduce Schematic: 1) do intra-node reduce, 2) do inter-node allreduce by CPU, 3) finally transfer reduced data to GPU. | ![](images/c0cdec69772c879b11c6dc8df5f84972f3f198146af3508df3ca47472992f12d.jpg) 图 6：HFReduce 原理图：1) 进行节点内归约，2) 由 CPU 进行跨节点 allreduce，3) 最后将归约后的数据传输回 GPU。 |

| 英文 | 中文 |
|------|------|
| GPUs within each node. This inter-node allreduce leverages a Double Binary Tree Algorithm [65], akin to NCCL, and is pipelined by dividing data into chunks for transfer via Remote Direct Memory Access (RDMA), ensuring high performance. HFReduce is versatile and can be applied to any scenario requiring allreduce, as well as general reduce and broadcast operations. | 这种跨节点 allreduce 采用与 NCCL 类似的双二叉树算法 [65]，并通过将数据分块，经远程直接内存访问（Remote Direct Memory Access, RDMA）进行流水线传输，从而保证高性能。HFReduce 具有通用性，可应用于任何需要 allreduce 的场景，以及通用的归约（reduce）和广播（broadcast）操作。 |

## A. HFReduce 算法步骤

| 英文 | 中文 |
|------|------|
| Intra-node reduction, as shown in the Algorithm 1: | 节点内归约，如算法 1 所示： |

| 英文 | 中文 |
|------|------|
| 1) When the gradients data on the GPUs require allreduce, HFReduce asynchronously transfers these data to the CPU memory. This Device-To-Host (D2H) Transfer can utilize GDRCopy [66] for small data and Mem-CpyAsync for larger data. | 1) 当 GPU 上的梯度数据需要 allreduce 时，HFReduce 异步地将这些数据传输到 CPU 内存。这种设备到主机（Device-To-Host, D2H）传输，小数据可利用 GDRCopy [66]，较大数据则用 MemCpyAsync。 |

| 英文 | 中文 |
|------|------|
| 2) Upon the arrival of the gradients in memory, perform reduction add operation using CPU vector instructions. | 2) 梯度到达内存后，使用 CPU 向量指令执行归约加操作。 |

| 英文 | 中文 |
|------|------|
| Inter-node reduction, as shown in the Algorithm 2: | 跨节点归约，如算法 2 所示： |

| 英文 | 中文 |
|------|------|
| 1) Use the Double Binary Tree Algorithm [65] for internode allreduce, facilitating transfers between nodes using RDMA verbs implementation. | 1) 使用双二叉树算法 [65] 进行跨节点 allreduce，通过 RDMA verbs 实现节点间传输。 |

| 英文 | 中文 |
|------|------|
| 2) Finally, the CPU returns reduced gradients to the GPU via PCIe (Host-To-Device Phase). | 2) 最后，CPU 通过 PCIe 将归约后的梯度返回给 GPU（主机到设备阶段）。 |

| 英文 | 中文 |
|------|------|
| The final Host-To-Device (H2D) Transfer can be optimized by utilizing GDRCopy to write data to four GPUs within the same NUMA node, effectively reducing reads from host memory by threefold compared to MemCpyAsync. This efficiency is achieved because GDRCopy can read data from host memory and temporarily cache it in the CPU caches, allowing data to be written to the four GPUs without additional reads from host memory. | 最终的主机到设备（Host-To-Device, H2D）传输可以通过使用 GDRCopy 将数据写入同一 NUMA 节点内的四块 GPU 来优化，相比 MemCpyAsync 可有效减少三倍的主机内存读取。这一效率得益于 GDRCopy 能从主机内存读取数据并临时缓存在 CPU 缓存中，从而无需额外读取主机内存即可将数据写入四块 GPU。 |

## B. HFReduce 相对于 NCCL 的优势（B. Advantages of HFReduce over NCCL）

| 英文 | 中文 |
|------|------|
| 1) Reduced PCIe Bandwidth Consumption: Let n be the total number of GPUs involved in the communication. In NCCL's ring topology, each unit of data needs to go through 2n – 1 transmissions, each consuming one unit of inbound | 1) 更少的 PCIe 带宽消耗：设 n 为参与通信的 GPU 总数。在 NCCL 的环形拓扑中，每单位数据需要经过 2n–1 次传输，每次消耗一块 GPU 的一单位入站带宽和另一块 GPU 的一单位出站带宽。 |

| 英文 | 中文 |
|------|------|
| ``` Algorithm 1: Intra Node Reduce.    Data: Dg: data need to allreduce    Result: Dc: data reduced in this node    1 Split Dg by Chunk\_Size    2 for Dg-i in Splited-Dg do    3 // Transfer GPU Memory Data to CPU    memory    4 Dc\_i = MemCopyAsync Dg\_i to CPU Mmeory    5 end    6 for i in Splited\_Count do    7 while every GPU's Dg\_i → Dc\_i finished do    8 // Wait for chunk-i transfer    finished in this node    9 for j in GPU\_Count do    10 // do intra-node reduce    11 Dc\_i += GPU-j's Dc\_i    12 end    13 // do inter-node reduce    14 Do\_Internode\_reduce(Dc\_i)    15 end    16 end ``` | ``` 算法 1：节点内归约。 输入：Dg：需要 allreduce 的数据 输出：Dc：本节点归约后的数据 1 按 Chunk_Size 切分 Dg 2 for Dg-i in Splited-Dg do 3     // 将 GPU 内存数据传输到 CPU 内存 4     Dc_i = MemCopyAsync Dg_i to CPU Memory 5 end 6 for i in Splited_Count do 7     while 本节点每个 GPU 的 Dg_i → Dc_i 传输完成 do 8         // 等待第 i 块 chunk 在本节点传输完成 9         for j in GPU_Count do 10            // 执行节点内归约 11            Dc_i += GPU-j 的 Dc_i 12        end 13        // 执行跨节点归约 14        Do_Internode_reduce(Dc_i) 15    end 16 end ``` |

| 英文 | 中文 |
|------|------|
| bandwidth of one GPU and one unit of outbound bandwidth of another GPU. This means for a single unit of data, it consumes 2n-1 unit of PCIe bidirectional bandwidth. In conn    trast, for each unit of data, HFReduce only requires one D2H and one H2D data transfer, only one unit of PCIe bidirectional bandwidth is consumed. In our machine architecture, the performance of NCCL is mainly limited by PCIe bandwidth. Therefore, HFReduce can achieve better performance than NCCL. | 这意味着单单位数据会消耗 2n–1 单位的 PCIe 双向带宽。相比之下，HFReduce 每单位数据只需一次 D2H 和一次 H2D 数据传输，仅消耗一单位 PCIe 双向带宽。在我们的机器架构中，NCCL 的性能主要受限于 PCIe 带宽。因此，HFReduce 能取得比 NCCL 更好的性能。 |

| 英文 | 中文 |
|------|------|
| 2) No GPU Kernel Overhead: HFReduce utilizes the GPU's Copy Engine (CE) for PCIe asynchronous transfers. In contrast, NCCL's allreduce operation requires GPU kernel execution, which can affect other computational kernels on the GPU. HFReduce achieves complete asynchrony with no overhead. | 2) 无 GPU 内核开销：HFReduce 利用 GPU 的复制引擎（Copy Engine, CE）进行 PCIe 异步传输。相比之下，NCCL 的 allreduce 操作需要执行 GPU 内核，这会影响 GPU 上其他计算内核的运行。HFReduce 实现了完全异步，且没有任何开销。 |

| 英文 | 中文 |
|------|------|
| As demonstrated in Figure 7a, HFReduce can reach a internode bandwidths of 6.3-8.1GB/s when performing allreduce with a data size of 186 MiB on the Fire-Flyer 2 AI-HPC, while NCCL's inter-node bandwidth is only 1.6-4.8GB/s. | 如图 7a 所示，在 Fire-Flyer 2 AI-HPC 上以 186 MiB 数据规模执行 allreduce 时，HFReduce 可达到 6.3–8.1GB/s 的跨节点带宽，而 NCCL 的跨节点带宽仅为 1.6–4.8GB/s。 |

## C. 性能改进：带 NVLink 的 HFReduce（C. Performance Improvements: HFReduce with NVLink）

| 英文 | 中文 |
|------|------|
| By installing the NVLink Bridge for PCIe A100 GPUs, efficient communication is enabled between paired GPUs via the 600 GB/s NVLink. To alleviate the memory bound issue of the original HFReduce, we implemented another allreduce pattern, termed HFReduce with NVLink. The core concept involves initially performing a reduction operation among GPUs interconnected by NVLink before passing the gradient to the CPU. Subsequently, when the CPU returns the result, it splits the result data and returns them to the paired GPUs connected by NVLink respectively, then performs allgather via NVLink. As illustrated in Figure 7b, HFReduce with NVLink achieves inter-node bandwidths exceeding 10 GB/s. | 通过为 PCIe A100 GPU 安装 NVLink 桥，成对 GPU 之间可通过 600 GB/s 的 NVLink 实现高效通信。为缓解原始 HFReduce 的内存瓶颈，我们实现了另一种 allreduce 模式，称为"带 NVLink 的 HFReduce"。其核心思路是：先将 NVLink 互连的 GPU 之间执行归约操作，再把梯度交给 CPU；随后，当 CPU 返回结果时，它将结果数据切分，分别返回给通过 NVLink 相连的成对 GPU，然后通过 NVLink 执行全收集。如图 7b 所示，带 NVLink 的 HFReduce 可实现超过 10 GB/s 的跨节点带宽。 |

| 英文 | 中文 |
|------|------|
| ![](images/25708247b2caca95e39c898a40a0e95fc888d0793d04e16a2a2763bee0084bc7.jpg)   (a) HFRudce and NCCL Allreduce Speed. | ![](images/25708247b2caca95e39c898a40a0e95fc888d0793d04e16a2a2763bee0084bc7.jpg) (a) HFReduce 与 NCCL 的 Allreduce 速度。 |

| 英文 | 中文 |
|------|------|
| ![](images/591cd9bcba07f4bff52f746fd1da3d7406cf5498fd8a322592cf702965858e80.jpg)   (b) HFReduce with NVLink (Cross Fat-Tree Zone). | ![](images/591cd9bcba07f4bff52f746fd1da3d7406cf5498fd8a322592cf702965858e80.jpg) (b) 带 NVLink 的 HFReduce（跨胖树区域）。 |

| 英文 | 中文 |
|------|------|
| Figure 7: Strong Scalability: (a) Network Bandwidth when HFReduce and NCCL do allreduce test with 186MiB data, scale from 16 to 1440 GPUs. (b) HFReduce with NVLink, and Cross Fat-Tree Zone. Note that tasks utilizing fewer than 128 GPUs do not require cross-zone nodes and are restricted by platform defaults. | 图 7：强扩展性：(a) HFReduce 与 NCCL 以 186MiB 数据执行 allreduce 测试时的网络带宽，规模从 16 块扩展到 1440 块 GPU。(b) 带 NVLink 的 HFReduce，以及跨胖树区域。注意，使用少于 128 块 GPU 的任务不需要跨区域节点，且受平台默认限制。 |

| 英文 | 中文 |
|------|------|
| ``` Algorithm 2: Inter Node Reduce.    Data: DL:local node reduced data by Algorithm 1    Data: DR: received other node reduced data    Result: Dg: reduced data transfer to GPU    1 // Pass 1: reduce data,individual    thread    2 for i in Chunk\_Size do    3 receive data DR\_i from prev node    4 if DL\_i ready then    5 DL\_i+=DR\_i// reduce data    6 end    7 if Thread is root of Tree then    8 send DL\_i to prev node / / Dg\_i    finished, go parse 2    9 else    10 send DL\_i to next node    11 end    12 end    13 / /    14 // Pass 2: gather reduced    data,individual thread    15 receive data DR\_i from next node    16 for j in GPU\_Count do    17 Dg\_i = MemCopyAsync DR\_i to GPU-j / / Dg\_i    is allreduced    18 end    19 send DL\_i to prev node ``` | ``` 算法 2：跨节点归约。 输入：DL：算法 1 得到的本节点归约数据 输入：DR：收到的其他节点归约数据 输出：Dg：传输给 GPU 的归约数据 1 // Pass 1：归约数据，单个线程 2 for i in Chunk_Size do 3     从上一节点接收数据 DR_i 4     if DL_i 已就绪 then 5         DL_i += DR_i   // 归约数据 6     end 7     if 本线程是树的根 then 8         将 DL_i 发送给上一节点 // Dg_i 完成，进入 Pass 2 9     else 10        将 DL_i 发送给下一节点 11    end 12 end 13 // 14 // Pass 2：收集归约后的数据，单个线程 15 从下一节点接收数据 DR_i 16 for j in GPU_Count do 17     Dg_i = MemCopyAsync DR_i to GPU-j // Dg_i 已是 allreduce 结果 18 end 19 将 DL_i 发送给上一节点 ``` |

## D. HFReduce 深入分析（D. Deep Analysis of HFReduce）

| 英文 | 中文 |
|------|------|
| 1) Key Technical Strategies in Implementation: | 1) 实现中的关键技术策略： |

| 英文 | 中文 |
|------|------|
| • Using GDRCopy accelerate small data transfer in D2H, and educing reads from host memory by three times compared to MemCpyAsyn. | • 使用 GDRCopy 加速 D2H 中的小数据传输，相比 MemCpyAsync 可减少三倍的主机内存读取。 |

| 英文 | 中文 |
|------|------|
| • Intra-Node Reduction: CPU utilizes SIMD instructions and supports FP32 / FP16 / BF16 / FP8 datatypes. | • 节点内归约：CPU 利用 SIMD 指令，支持 FP32 / FP16 / BF16 / FP8 数据类型。 |

| 英文 | 中文 |
|------|------|
| • NUMA Awareness: D2H destination memory is interleaved across two NUMA nodes for maximum bandwidth. Memory for CPU-added results and networkreceived data is bound to the IB-Nic's NUMA node to minimize latency. | • NUMA 感知：D2H 的目标内存交错分布到两个 NUMA 节点，以获得最大带宽。CPU 相加结果与网络接收数据的内存绑定到 IB 网卡的 NUMA 节点，以最小化延迟。 |

| 英文 | 中文 |
|------|------|
| • Inter-Node Reduce:Implements a Double Binary Tree allreduce algorithm [65] via ibverbs RDMA Write, avoiding additional overhead. | • 跨节点归约：通过 ibverbs RDMA 写实现双二叉树 allreduce 算法 [65]，避免额外开销。 |

| 英文 | 中文 |
|------|------|
| 2) HFReduce Overcomes Limitations of EPYC Rome CPU: We consulted AMD and NVIDIA engineers to identify the root cause of NCCL's suboptimal performance on PCIe architecture, particularly with EPYC Rome CPU servers. It was determined that the Rome CPUs do not support the chained write feature, which can significantly accelerate PCIe peer-topeer (P2P) transfers between GPUs and IB NICs. Our tests indicate that the maximum bandwidth between the GPU and IB NIC on Rome CPUs is approximately 9 GiB/s, making the observed 4GB/s all-reduce bandwidth for NCCL understandable. HFReduce circumvents this limitation by utilizing the CPU for reduction and transferring data through IB and host memory. | 2) HFReduce 克服 EPYC Rome CPU 的局限：我们咨询了 AMD 和 NVIDIA 工程师，以找出 NCCL 在 PCIe 架构（尤其是 EPYC Rome CPU 服务器）上性能不佳的根源。确定原因是 Rome CPU 不支持链式写（chained write）特性，而该特性可显著加速 GPU 与 IB 网卡之间的 PCIe 对等（peer-to-peer, P2P）传输。我们的测试表明，Rome CPU 上 GPU 与 IB 网卡之间的最大带宽约为 9 GiB/s，因此 NCCL 仅 4GB/s 的全归约带宽也就不难理解了。HFReduce 通过利用 CPU 进行归约、并经由 IB 和主机内存传输数据，绕开了这一限制。 |

| 英文 | 中文 |
|------|------|
| 3) Bottlenecks of HFReduce: When considering the total memory operations on a single node during HFReduce, several factors contribute to its performance limitations: | 3) HFReduce 的瓶颈：当考虑 HFReduce 过程中单个节点上的总内存操作时，以下几个因素限制了其性能： |

| 英文 | 中文 |
|------|------|
| 1) D2H Phase requires 8 write operations. | 1) D2H 阶段需要 8 次写操作。 |

| 英文 | 中文 |
|------|------|
| 2) Intra-node Reduce Add Phase involves 8 read operations and 1 write operation. | 2) 节点内归约加阶段涉及 8 次读操作和 1 次写操作。 |

| 英文 | 中文 |
|------|------|
| 3) Inter-node Allreduce Phase: IB send demands 2 read operations, while IB receive requires 2 write operations, along with 1 read operation for reduce add. | 3) 跨节点 allreduce 阶段：IB 发送需要 2 次读操作，而 IB 接收需要 2 次写操作，外加 1 次归约加读操作。 |

| 英文 | 中文 |
|------|------|
| 4) H2D Phase Utilizing GDRCopy can reduce this to only 2 read operations, whereas MemCopy necessitates 8 read operations. | 4) 利用 GDRCopy 的 H2D 阶段可将读取降至仅 2 次，而 MemCopy 需要 8 次读操作。 |

| 英文 | 中文 |
|------|------|
| In total, the memory operations amount to 24 times the original data size in the GPU. A host equipped with 16 channels of DDR4-3200MHz memory can achieve a practical memory access speed of 320GB/s. Consequently, the theoretical maximum speed of HFReduce is approximately 13.3GB/s, but when considering the allreduce algorithm bandwidth and network bandwidth, this value realistically approximates 12GB/s. However, our tests only achieved slightly over 8GB/s. | 总体上，内存操作总量是 GPU 内原始数据大小的 24 倍。配备 16 通道 DDR4-3200MHz 内存的主机可实现约 320GB/s 的实际内存访问速度。因此，HFReduce 的理论最大速度约为 13.3GB/s，但考虑到 allreduce 算法的带宽与网络带宽，该值实际约为 12GB/s。然而，我们的测试仅达到略高于 8GB/s。 |

| 英文 | 中文 |
|------|------|
| The root cause of this discrepancy is another limitation of the EPYC CPUs. As previously mentioned, our GPU5 and | 造成这一差距的根源是 EPYC CPU 的另一个局限。如前所述，我们的 GPU5 和 |

| 英文 | 中文 |
|------|------|
| ![](images/226754bc71f089751e61fcaeda4c2022e3e1cce71b5a6d0963155670c4a85918.jpg)   (a) HFReduce v.s. Torch DDP. | ![](images/226754bc71f089751e61fcaeda4c2022e3e1cce71b5a6d0963155670c4a85918.jpg) (a) HFReduce 对比 Torch DDP。 |

| 英文 | 中文 |
|------|------|
| ![](images/339ea0acf5f74c4bf77677e6a3bcae5a917b3bcae7f943fee4d79c67eafca80a.jpg)   (b) HaiScale v.s. Torch FSDP. | ![](images/339ea0acf5f74c4bf77677e6a3bcae5a917b3bcae7f943fee4d79c67eafca80a.jpg) (b) HaiScale 对比 Torch FSDP。 |

| 英文 | 中文 |
|------|------|
| Figure 8: Weak Scalability: (a) Training VGG16, HFReduce compared to PyTorch DDP's NCCL backend (b) Training GPT2-Medium HaiScale compared to Torch, both using FSDP. | 图 8：弱扩展性：(a) 训练 VGG16，HFReduce 对比 PyTorch DDP 的 NCCL 后端 (b) 训练 GPT2-Medium，HaiScale 对比 Torch，两者均使用 FSDP。 |

| 英文 | 中文 |
|------|------|
| GPU6 are directly connected to the CPU via the same PCIe Root Complex Port (also known as the PCIe Host Bridge). In AMD EPYC Rome and Milan CPUs, the maximum bandwidth from the Root Complex Port to the CPU's internal bus is about 37.5GB/s. Although a PCIe 4.0 x16 port can achieve over 27GB/s from GPU to CPU, when two GPUs transfer data concurrently, the bandwidth is limited to around 37GB/s. Furthermore, if bidirectional data transfer occurs simultaneously, this bandwidth decreases even further. As a result, HFReduce does not reach its theoretical speed. | GPU6 通过同一个 PCIe 根复合体端口（也称为 PCIe 主机桥）直接连接到 CPU。在 AMD EPYC Rome 和 Milan CPU 中，根复合体端口到 CPU 内部总线的最大带宽约为 37.5GB/s。虽然 PCIe 4.0 x16 端口从 GPU 到 CPU 可实现超过 27GB/s 的带宽，但当两块 GPU 并发传输数据时，带宽被限制在约 37GB/s 左右。此外，如果同时发生双向数据传输，带宽还会进一步下降。因此，HFReduce 无法达到其理论速度。 |

| 英文 | 中文 |
|------|------|
| Employing NVLink with HFReduce offers a functional method to alleviate these bottlenecks. However, it is worth noting that the next-generation CPUs, such as the EPYC Genoa, still face issues with PCIe Host Bridge bandwidth, which cannot support two full-speed PCIe ports simultaneously. We hope AMD will address this issue in future iterations. | 将 NVLink 与 HFReduce 结合使用，为缓解这些瓶颈提供了一种有效方法。但值得注意的是，下一代 CPU（如 EPYC Genoa）在 PCIe 主机桥带宽方面仍存在问题，无法同时支持两个全速的 PCIe 端口。我们希望 AMD 能在未来版本中解决这一问题。 |

## V. HAISCALE：面向深度学习模型训练的特殊优化

## A. HaiScale DDP 在训练中重叠 AllReduce（A. HaiScale DDP Overlap AllReduce in Training）

| 英文 | 中文 |
|------|------|
| HaiScale Distributed Data Parallel (DDP) is a training tool that utilizes HFReduce as its communication backend, in contrast to PyTorch's DDP [67] which employs NCCL as its backend. During the backpropagation phase, HaiScale DDP performs an asynchronous allreduce operation on the computed gradients, allowing this communication to overlap with the computation involved in backpropagation. | HaiScale 分布式数据并行（Distributed Data Parallel, DDP）是一种训练工具，它使用 HFReduce 作为通信后端，这与使用 NCCL 作为后端的 PyTorch DDP [67] 形成对比。在反向传播阶段，HaiScale DDP 对计算出的梯度执行异步 allreduce 操作，使这种通信能与反向传播中的计算相互重叠。 |

| 英文 | 中文 |
|------|------|
| As previously mentioned, HFReduce does not depend on GPU Streaming Multiprocessors (SM) for reduction computation, enabling completely asynchronous allreduce without impacting performance. As shown in Figure 8a, training VGG16 model [68] with HFReduce takes only half the time compared to using Torch DDP's NCCL backend, achieving nearly 88% parallel scalability when scale from 32 GPUs to 512. | 如前所述，HFReduce 不依赖 GPU 流式多处理器（Streaming Multiprocessor, SM）进行归约计算，因此可以实现完全异步的 allreduce 而不会影响性能。如图 8a 所示，使用 HFReduce 训练 VGG16 模型 [68] 仅需使用 Torch DDP 的 NCCL 后端的一半时间，并且从 32 块 GPU 扩展到 512 块时，实现了近 88% 的并行可扩展性。 |

## B. LLM 训练优化

| 英文 | 中文 |
|------|------|
| Our HaiScale framework various parallelism strategies for training large language models (LLMs), similar to Megagron [69] and DeepSpeed [70]. We have made specific engineering optimizations for our PCIe architecture across Data Parallelism (DP), Pipeline Parallelism (PP) [11] [12], Tensor Parallelism (TP) [14], Expert Parallelism (EP) [15]–[17]. | 我们的 HaiScale 框架提供了多种用于训练大语言模型（LLM）的并行策略，与 Megatron [69] 和 DeepSpeed [70] 类似。我们针对 PCIe 架构，在数据并行（DP）、流水线并行（PP）[11] [12]、张量并行（TP）[14]、专家并行（EP）[15]–[17] 方面做了具体的工程优化。 |

| 英文 | 中文 |
|------|------|
| ![](images/5ff71d372d3a03e139f138d1c8f0901871fc42b5dbc309fb8260573894eecc3b.jpg) | ![](images/5ff71d372d3a03e139f138d1c8f0901871fc42b5dbc309fb8260573894eecc3b.jpg) |

| 英文 | 中文 |
|------|------|
| ![](images/48c29dfa269fdd0ef3ce3d08badfdce41a5996b6c6ed5443c410cefddb52135d.jpg)   (a) Train LLaMa-13B   (b) Train DeepSeekMoE-16B   Figure 9: Strong Scalability: (a) Train LLaMa-13B with a config of sequence length 2048, batch size 4096, pipeline parallel 4. (b)Train DeepSeekMoE-16B with a config of sequence length 4096, batch size 4608, pipeline parallel 10. | ![](images/48c29dfa269fdd0ef3ce3d08badfdce41a5996b6c6ed5443c410cefddb52135d.jpg) (a) 训练 LLaMa-13B (b) 训练 DeepSeekMoE-16B 图 9：强扩展性：(a) 以序列长度 2048、批量大小 4096、流水线并行度 4 的配置训练 LLaMa-13B。(b) 以序列长度 4096、批量大小 4608、流水线并行度 10 的配置训练 DeepSeekMoE-16B。 |

| 英文 | 中文 |
|------|------|
| 1) NVLink Bridge Enables Tensor Parallel between PCIe GPUs: With the advent of LLMs, we integrated the NVLink Bridge into our system. This addition established a bandwidth of 600GB/s between each pair of GPUs, enabling more efficient when performing Tensor Parallelism. | 1) NVLink 桥使 PCIe GPU 之间实现张量并行：随着 LLM 的到来，我们将 NVLink 桥集成到系统中。这一新增使得每对 GPU 之间建立起 600GB/s 的带宽，在执行张量并行时更加高效。 |

| 英文 | 中文 |
|------|------|
| 2) Pipeline Parallelism Optimization in PCIe Architecture: In our architecture, there is only one IB NIC for 8 GPUs on a single node, which can lead to network bandwidth contention during Pipeline Parallelism (PP). We solve this by configuring Data Parallelism (DP) rank, making the 8 GPUs on the same node belong to different DP ranks which staggers the timing of PP for each DP rank. As Figure 9a shown, when scaling from 64 GPUs to 512 GPUs, the step time of training LLaMa-13B [71] decreases from 64.118 seconds to 9.717 seconds achieving a parallel efficiency of 91%. | 2) PCIe 架构中的流水线并行优化：在我们的架构中，单个节点上 8 块 GPU 只有一块 IB 网卡，这在流水线并行（PP）期间可能导致网络带宽争用。我们通过配置数据并行（DP）的 rank 来解决这一问题，使同一节点上的 8 块 GPU 分属不同的 DP rank，从而错开各 DP rank 的 PP 时机。如图 9a 所示，当从 64 块 GPU 扩展到 512 块 GPU 时，训练 LLaMa-13B [71] 的步耗时从 64.118 秒降至 9.717 秒，并行效率达 91%。 |

| 英文 | 中文 |
|------|------|
| We also benchmarked the training performance of our DeepSeekMoE-16B model [72] on Fire-Flyer 2 AI-HPC. As shown in Figure 9b, scaling from 40 GPUs to 640 GPUs reduced the time per training step from 79.615 seconds to 6.535 seconds, achieving a parallel efficiency of 76.14%. Notably, with 320 GPUs, the step time was 10.71 seconds, resulting in a parallel efficiency of 92.92%, demonstrating excellent scalability. | 我们还在 Fire-Flyer 2 AI-HPC 上对我们的 DeepSeekMoE-16B 模型 [72] 进行了训练性能基准测试。如图 9b 所示，从 40 块 GPU 扩展到 640 块 GPU，每训练步耗时从 79.615 秒降至 6.535 秒，并行效率达 76.14%。值得注意的是，在 320 块 GPU 时，步耗时为 10.71 秒，并行效率达 92.92%，展现出优异的可扩展性。 |

| 英文 | 中文 |
|------|------|
| 3) Fully Sharded Data Parallel (FSDP): Both HaiScale's FSDP and PyTorch's FSDP [18] are implementations based on the ZeRO Stage-3 algorithm [19]. The details of this implementation are already discussed in Section II-B1. | 3) 全分片数据并行（FSDP）：HaiScale 的 FSDP 与 PyTorch 的 FSDP [18] 都是基于 ZeRO Stage-3 算法 [19] 的实现。该实现的细节已在第二节-B1 中讨论。 |

| 英文 | 中文 |
|------|------|
| HaiScale's FSDP offers better engineering implementation, optimizing memory management to reduce fragmentation specific to model adjustments. And we overlap allgather and reduce-scatter communication with forward and backward computation, split the optimization step during backward propagation for enhanced overlap. As shown in Figure 8b, training GPT2-medium [73], we achieve 95% parallel scalability when scaling from 16 to 128 GPUs. ompared to PyTorch's FSDP, HaiScale's FSDP reduces training time by nearly half. | HaiScale 的 FSDP 提供了更好的工程实现，通过优化内存管理来减少针对模型调整产生的碎片。我们将全收集与归约散播通信与前向、反向计算重叠，并在反向传播期间拆分优化步骤以增强重叠。如图 8b 所示，训练 GPT2-medium [73] 时，从 16 块扩展到 128 块 GPU 实现了 95% 的并行可扩展性。与 PyTorch 的 FSDP 相比，HaiScale 的 FSDP 将训练时间缩短了近一半。 |

## C. 小结

| 英文 | 中文 |
|------|------|
| Our AI-HPC design meets DL requirements, and with the addition of the NVLink Bridge, it meets the training needs of early-stage LLMs, reaching the utilization upper limit of PCIe GPUs. However, due to the inherent gap between PCIe card specifications and SXM, there is a certain performance discrepancy. Considering overall performance, basic setup cost, and energy consumption, we achieved 80% performance at half the cost. We believe Fire-Flyer 2 AI-HPC is a successful practice in terms of cost-effectiveness. | 我们的 AI-HPC 设计满足深度学习需求，而随着 NVLink 桥的加入，它满足了早期 LLM 的训练需求，达到了 PCIe GPU 的利用率上限。然而，由于 PCIe 卡与 SXM 在规格上的固有差距，仍存在一定的性能差异。综合性能、基础建设成本与能耗考虑，我们以一半的成本实现了 80% 的性能。我们认为 Fire-Flyer 2 AI-HPC 在成本效益方面是一次成功的实践。 |

## VI. 先进的高性价比与协同设计优化

## A. 确保我们的计算存储一体化网络拥塞最小化

| 英文 | 中文 |
|------|------|
| As previously stated, our cost-effective network integrated computation communication and storage traffics together. To achieve maximum bandwidth, it is essential to isolate interference between different types of traffic and control network congestion. In practice, we implemented the following measures: | 如前所述，我们高性价比的网络将计算通信与存储流量一体化。为获得最大带宽，必须隔离不同类型流量之间的相互干扰，并控制网络拥塞。在实践中，我们采取了以下措施： |

| 英文 | 中文 |
|------|------|
| 1) Divergence of Different Traffics: In typical training tasks, there are four different types of traffic: HFReduce communication, NCCL communication, 3FS storage traffic, and other traffic. By using InfiniBand's Service Level (SL) technology [74] [75], we assign different value of SL when establishing connections between nodes and map SL to IB physical queues Virtual Lanes (VLs) [74] [75]. The use of Virtual Lanes ensures that flows in distinct lanes do not interfere with each other. Ultimately, we configured their proportions to implement traffic isolation, thereby preventing network congestion caused by Head-of-line (HOL) blocking [76] and different traffic collisions. | 1) 不同流量的分流：在典型训练任务中，存在四种不同类型的流量：HFReduce 通信、NCCL 通信、3FS 存储流量以及其他流量。通过使用 InfiniBand 的服务等级（Service Level, SL）技术 [74] [75]，我们在节点间建立连接时为不同流量分配不同的 SL 值，并将 SL 映射到 IB 的物理队列虚拟通道（Virtual Lanes, VLs）[74] [75]。虚拟通道的使用确保不同通道中的流互不干扰。最终，我们配置它们的比例以实现流量隔离，从而防止队头（Head-of-line, HOL）阻塞 [76] 和不同流量冲突导致的网络拥塞。 |

| 英文 | 中文 |
|------|------|
| 2) Topology Adjustment and Route Optimization: In highthroughput storage scenarios, there naturally exist many incast communication patterns, leading to certain congestion in the network. Under such circumstances, we observed that enabling adaptive routing would lead to more severe congestion spread in the network. Therefore, we opted for a static routing strategy. Based on the static routing scheme, to evenly disperse storage traffic into leaf → spine links, we distribute various nodes (storage, computation, management nodes) evenly disperse storage traffic into leaf → spine links. | 2) 拓扑调整与路由优化：在高吞吐存储场景中，天然存在许多 incast 通信模式，会在网络中造成一定拥塞。在这种情况下，我们观察到启用自适应路由反而会导致更严重的拥塞扩散。因此，我们选择了静态路由策略。基于静态路由方案，为将存储流量均匀分散到叶 → 脊链路，我们将各种节点（存储、计算、管理节点）均匀分散布置，使存储流量均匀分布到叶 → 脊链路。 |

| 英文 | 中文 |
|------|------|
| 3) NCCL Optimization: We adjusted the NCCL topology to route through the IB NIC and GPUs within the same NUMA node. This adjustment reduced PCIe congestion caused by CPU chiplet interconnects. Additionally, by using PCIe Relaxed Ordering [77], we further reduced congestion and increased bandwidth. | 3) NCCL 优化：我们调整了 NCCL 拓扑，使其通过同一 NUMA 节点内的 IB 网卡和 GPU 路由。这一调整减少了由 CPU 芯粒间互联（chiplet interconnect）造成的 PCIe 拥塞。此外，通过使用 PCIe 松弛排序（Relaxed Ordering）[77]，我们进一步减少了拥塞并提高了带宽。 |

| 英文 | 中文 |
|------|------|
| 4) Network Tuning in 3FS: 3FS implements a request-tosend control mechanism to mitigate the congestion. Details are discussed in the next subsection, Key Techinical Points of 3FS. | 4) 3FS 中的网络调优：3FS 实现了请求-发送（request-to-send）控制机制以缓解拥塞。具体细节在下一小节"3FS 关键技术要点"中讨论。 |

## B. 高吞吐分布式文件系统：3FS（B. High-Throughput Distributed File System: 3FS）

| 英文 | 中文 |
|------|------|
| 1) Overview: 3FS is our in-house developed high performance distributed file system, akin to WekaFS [78], DAOS [79], [80], and BeeGFS [81]. However, the design and implementation of 3FS specifically focus on fully utilizing the high IOPS and throughput of NVMe SSDs and the RDMA network. | 1) 概述：3FS 是我们自研的高性能分布式文件系统，类似于 WekaFS [78]、DAOS [79]、[80] 和 BeeGFS [81]。然而，3FS 的设计与实现专门聚焦于充分利用 NVMe SSD 的高 IOPS 与吞吐量以及 RDMA 网络。 |

| 英文 | 中文 |
|------|------|
| Table IV: Storage Node Hardware Details | 表 IV：存储节点硬件细节 |

**英文表**

| CPU | 1 * AMD 64 Cores EPYC 7742 CPU |
| --- | --- |
| Memory | 512GB 8-Channels DDR4-3200Mhz |
| NICs | 2 * Mellanox InfiniBand CX6 200Gbps NIC |
| Data SSDs | 16 *15.36TB PCIe 4.0x4 |

**中文表**

| | |
|---|---|
| CPU | 1 \* AMD 64 核 EPYC 7742 CPU |
| 内存 | 512GB 8 通道 DDR4-3200Mhz |
| 网卡 | 2 \* Mellanox InfiniBand CX6 200Gbps 网卡 |
| 数据 SSD | 16 \* 15.36TB PCIe 4.0x4 |

| 英文 | 中文 |
|------|------|
| 2) 3FS Storage Node Hardware: In Fire-Flyer 2 AI-HPC, we deployed 180 storage nodes, as shown in Table IV, each node contains 16 PCIe 4.0 NVMe SSDs and 2 Mellanox CX6 200Gbps InfiniBand HCAs. With totally 360 \* 200Gbps outbound InfiniBand HCAs, the system can total provide 9TB/s outbound bandwidh, and we actually achieved total read throughput of 8TB/s. The total 2880 NVMe SSDs provide over 20PiB storage space with an mirror data redundancy. | 2) 3FS 存储节点硬件：在 Fire-Flyer 2 AI-HPC 中，我们部署了 180 个存储节点，如表 IV 所示，每个节点包含 16 块 PCIe 4.0 NVMe SSD 和 2 块 Mellanox CX6 200Gbps InfiniBand HCA。凭借总计 360 \* 200Gbps 的出向 InfiniBand HCA，系统可提供总计 9TB/s 的出向带宽，而我们实际实现了 8TB/s 的总读吞吐量。总计 2880 块 NVMe SSD 提供超过 20PiB 的存储空间，并带有镜像数据冗余。 |

| 英文 | 中文 |
|------|------|
| 3) Key Techinical Points of 3FS: The 3FS system comprises four roles: cluster manager, meta service, storage service and client. Meta and storage services send heartbeats to cluster manager. All services and clients poll cluster configuration and service status from the manager. Multiple cluster managers are present, with one elected as the primary. | 3) 3FS 关键技术要点：3FS 系统由四种角色组成：集群管理器、元数据服务、存储服务和客户端。元数据与存储服务向集群管理器发送心跳。所有服务与客户端从管理器轮询集群配置与服务状态。系统中有多个集群管理器，其中一个被选举为主管理器。 |

| 英文 | 中文 |
|------|------|
| File system meta data are stored in tables of a distributed key-value storage system. Each file or directory has a unique inode ID. The File inode/directory ID and meta data, such as file size and location information of the file content data, are stored as key-value pairs in the inode table. A separate directory entry table stores key-value pairs of (parent\_dir\_inode\_id, entry\_name) : (entry\_inode\_id, ...) to support iterating entries in a directory and resolving file/directory paths. All states of meta services are persisted on the distributed key-value storage system. Several meta services run concurrently to handle meta requests from clients. | 文件系统元数据存储在分布式键值存储系统的表中。每个文件或目录都有一个唯一的 inode ID。文件 inode/目录 ID 以及元数据（如文件大小和文件内容数据的位置信息）以键值对的形式存储在 inode 表中。另一个独立的目录项表存储 (parent_dir_inode_id, entry_name) : (entry_inode_id, ...) 键值对，以支持目录项的迭代遍历以及文件/目录路径的解析。元数据服务的所有状态都持久化在分布式键值存储系统上。多个元数据服务并发运行，以处理来自客户端的元数据请求。 |

| 英文 | 中文 |
|------|------|
| The storage service has an implementation of Chain Replication with Apportioned Queries (CRAQ) [82] to provide strong consistency. CRAQ's write-all-read-any approach helps to unleash the throughput and IOPS of all SSDs. File content are split into chunks, which are replicated over a chain of storage targets. A chain table contains an ordered set of chains. The meta service selects an offset in the chain table and a stripe size k for each file. The file chunks are assigned to the next k chains starting at the offset. To distribute read/write traffic evenly to all SSDs, each SSD serves multiple storage targets from different chains. The storage service runs on every storage node and manages a few storage targets. | 存储服务实现了带分配查询的链式复制（Chain Replication with Apportioned Queries, CRAQ）[82]，以提供强一致性。CRAQ 的"写全部-读任意"（write-all-read-any）方法有助于释放所有 SSD 的吞吐量与 IOPS。文件内容被切分为块（chunk），这些块在存储目标链上进行复制。链表中包含一个有序的链集合。元数据服务为每个文件在链表中选择一个偏移量和一个条带大小 k。文件块被分配到从该偏移量开始的后续 k 条链上。为将读写流量均匀分布到所有 SSD，每块 SSD 服务于来自不同链的多个存储目标。存储服务运行在每个存储节点上，管理若干个存储目标。 |

| 英文 | 中文 |
|------|------|
| The storage network has a Fat-Tree topology that provides full bisection bandwidth. By design, each 3FS client can access every storage service. At peak load, incast congestion is observed on the client side. To mitigate this congestion, a request-to-send control mechanism is implemented in storage service and client [83]. After receiving a read request from a client, the service reads data from SSD and asks the client's permission to transfer the data. The client limits the number of concurrent senders. When a storage service is granted the permission to transfer, it sends the data with a RDMA WRITE followed by a RDMA SEND to notify the client. The request-to-send control increases end-to-end IO latency but it's required to achieve sustainable high throughput. | 存储网络采用胖树拓扑，提供全对分带宽。按设计，每个 3FS 客户端都能访问每一个存储服务。在峰值负载时，客户端侧会观察到 incast 拥塞。为缓解这种拥塞，存储服务与客户端实现了一种请求-发送控制机制 [83]。服务端收到客户端的读请求后，从 SSD 读取数据，并请求客户端允许传输数据。客户端限制并发的发送者数量。当存储服务获得传输许可后，它以一次 RDMA 写随后一次 RDMA 发送的方式发送数据，以通知客户端。请求-发送控制会增加端到端的 I/O 延迟，但它是实现可持续高吞吐所必需的。 |

| 英文 | 中文 |
|------|------|
| 4) 3FS-KV: 3FS-KV is a shared-storage distributed data processing system built on top of 3FS, currently supporting three models: key-value, message queue, and object storage. It supports read-write separation and on-demand startup, allowing it to fully leverage the extremely high I/O throughput provided by 3FS. 3FS-KV supports DeepSeek's KV Context Caching on Disk technology [84], which reduces the cost of LLM serving by an order of magnitude. | 4) 3FS-KV：3FS-KV 是构建在 3FS 之上的共享存储分布式数据处理系统，目前支持三种模型：键值、消息队列与对象存储。它支持读写分离与按需启动，从而能充分利用 3FS 提供的极高 I/O 吞吐。3FS-KV 支持 DeepSeek 的 KV 上下文磁盘缓存（KV Context Caching on Disk）技术 [84]，将 LLM 推理服务的成本降低了一个数量级。 |

## C. HAI 平台：一个分时调度平台

| 英文 | 中文 |
|------|------|
| The principle of time-sharing scheduling is applied to cluster resource management. Users submit tasks, such as running Python / bash code, starting development containers, etc., and the platform interrupts and loads tasks according to current resource requirements, cluster busyness, etc. Task code needs to follow the platform coding rules to ensure that it can be continued from breakpoints, with the specific process as follows: | 分时调度的原理被应用于集群资源管理。用户提交任务，如运行 Python / bash 代码、启动开发容器等，平台根据当前资源需求、集群繁忙程度等中断和加载任务。任务代码需要遵循平台编码规则，以确保能从断点继续运行，具体流程如下： |

| 英文 | 中文 |
|------|------|
| • Accepting the interruption signal from the cluster; | • 接收来自集群的中断信号； |

| 英文 | 中文 |
|------|------|
| • Saving checkpoints (model parameters, optimizer parameters, etc.); | • 保存检查点（模型参数、优化器参数等）； |

| 英文 | 中文 |
|------|------|
| • Notifying the cluster of interruptions; | • 通知集群已中断； |

| 英文 | 中文 |
|------|------|
| • Recovering from the checkpoint and continuing to run. | • 从检查点恢复并继续运行。 |

| 英文 | 中文 |
|------|------|
| The cluster deploying HAI Platform does not pool GPU resources, but classifies and marks them based on computing nodes as basic units, according to resource types, network areas, etc. The HAI Platform encourages users to fully utilize multiple GPUs simultaneously for parallel training, facilitating 99% utilization. | 部署 HAI 平台的集群不进行 GPU 资源池化，而是以计算节点为基本单位，按资源类型、网络区域等对节点进行分类与标记。HAI 平台鼓励用户同时充分利用多块 GPU 进行并行训练，促成了 99% 的利用率。 |

## VII. 稳定性与鲁棒性

## A. 检查点管理器

| 英文 | 中文 |
|------|------|
| Training LLMs can span several months, during which unavoidable hardware failures may cause training interruptions. To minimize recovery time and support the HAI Platform's interrupt and recovery operations, we developed a checkpoint manager. Additionally, the substantial size of LLM checkpoints necessitated an efficient method for saving and loading them, leveraging the high throughput of 3FS. The checkpoint manager includes the following components: | 训练 LLM 可能持续数月，期间不可避免的硬件故障可能导致训练中断。为最大限度地缩短恢复时间，并支持 HAI 平台的中断与恢复操作，我们开发了一个检查点管理器。此外，LLM 检查点体量巨大，需要一种高效的方法来保存和加载它们，而这正好利用了 3FS 的高吞吐。检查点管理器包含以下组件： |

| 英文 | 中文 |
|------|------|
| • Parameters and optimization states are divided into chunks and written to 3FS using the 3FS batch write API, which is significantly faster than normal writes, achieving over 10 GiB/s per node. This enables saving to be completed in just a few seconds. | • 参数与优化器状态被划分为块，并使用 3FS 的批量写 API 写入 3FS，这比普通写入显著更快，每个节点可超过 10 GiB/s。这使得保存只需几秒钟即可完成。 |

| 英文 | 中文 |
|------|------|
| • Parameters and optimization states are asynchronously transferred from GPU to CPU host memory, with checkpoint saving performed periodically (typically every 5 minutes). | • 参数与优化器状态被异步地从 GPU 传输到 CPU 主机内存，并周期性执行检查点保存（通常每 5 分钟一次）。 |

| 英文 | 中文 |
|------|------|
| • During the saving process, each tensor is recorded with its index and the offset within the checkpoint., which makes the location of tensors more convenient during the loading process. With the 3FS batch read API, a loading process can be completed in just a few seconds. | • 在保存过程中，每个张量都记录其索引以及检查点内的偏移量，这使得加载过程定位张量更加方便。借助 3FS 的批量读 API，加载过程只需几秒钟即可完成。 |

| 英文 | 中文 |
|------|------|
| Thanks to the high write throughput of 3FS, periodic saving operations can be completed asynchronously in a matter of seconds, without impacting the training process. In the event of hardware failures that interrupt training, only the last 5 minutes of progress are lost. For a cluster with thousands of nodes, this overhead from disaster recovery is minimal. | 得益于 3FS 的高写入吞吐，周期性保存操作可以在数秒内异步完成，而不会影响训练过程。一旦发生硬件故障中断训练，最多只会丢失最后 5 分钟的进度。对于拥有数千节点的集群而言，这种容灾开销微乎其微。 |

## B. 校验器

| 英文 | 中文 |
|------|------|
| The best way to enhance device stability is to identify issues before they occur. Therefore, we have developed a set of validator tools to verify whether the hardware is functioning correctly. The platform's automatic operation and maintenance system runs the validator program weekly on nodes to verify their proper functionality. It removes the faulty nodes from the scheduling platform, ensuring that all scheduled nodes are operational. Diagnosing tools like hostping [85] also integrated in our platform, but to find root cause of Hardware Failures is still hard work for operation teams. The validator mainly consists of the following parts: | 提升设备稳定性的最佳方式是在问题发生之前就发现它们。因此，我们开发了一套校验器工具，用于验证硬件是否正常工作。平台的自动化运维系统每周在节点上运行校验程序，以验证其功能正常。它会将有故障的节点从调度平台中移除，确保所有被调度的节点都处于可用状态。hostping [85] 等诊断工具也集成在我们的平台中，但要找出硬件故障的根因，对运维团队而言仍是一项艰巨工作。校验器主要由以下几部分组成： |

| 英文 | 中文 |
|------|------|
| • Checking hardware frequency, link speed, and link status. | • 检查硬件频率、链路速率与链路状态。 |

| 英文 | 中文 |
|------|------|
| • Testing CPU stress and memory bandwidth. | • 测试 CPU 压力与内存带宽。 |

| 英文 | 中文 |
|------|------|
| • GPU Memory test: This involves checking each byte of GPU memory to ensure no data corruption has occurred. | • GPU 内存测试：逐字节检查 GPU 内存，确保未发生数据损坏。 |

| 英文 | 中文 |
|------|------|
| • Running GEMM with full GPU memory occupancy, which can simultaneously check whether there are any operational logic faults in the GPU chip. | • 以满 GPU 内存占用运行 GEMM，可同时检查 GPU 芯片是否存在运行逻辑故障。 |

| 英文 | 中文 |
|------|------|
| • Intra-node allreduce test: checking NVLink bandwidth through upper-level applications. | • 节点内 allreduce 测试：通过上层应用检查 NVLink 带宽。 |

| 英文 | 中文 |
|------|------|
| • Storage bandwidth stress test to make sure storage is functioning normally. | • 存储带宽压力测试，确保存储正常工作。 |

## C. Fire-Flyer 2 AI-HPC 中的硬件故障特征（C. Hardware Failures Characterization in Fire-Flyer 2 AI-HPC）

| 英文 | 中文 |
|------|------|
| In supercomputers and data centers, hardware failures and chip errors can lead to floating-point overflow, nonconvergence, or slow convergence during model training [86]. This paper [87] even directly points out that there is a substantial amount of Silent Data Corruption in data center processors, ultimately leading to a variety of complex issues that are difficult to replicate and locate. Indeed, in our practice, we have encountered computational errors and GPU memory errors not detected by Error Correction Code (ECC), which led to models’ gradnorm spikes, loss explosions and even nonconvergence. How to tackle these hardware failures, promptly identify and categorize them, is a key issue to improve the online rate and overall utilization of cluster nodes. | 在超级计算机和数据中心中，硬件故障与芯片错误可能导致模型训练中的浮点溢出、不收敛或收敛缓慢 [86]。文献 [87] 甚至直接指出，数据中心处理器中存在大量静默数据损坏（Silent Data Corruption），最终导致各种难以复现与定位的复杂问题。确实，在我们的实践中，我们遇到过纠错码（ECC）未检测到的计算错误和 GPU 内存错误，它们导致了模型梯度范数尖峰、损失爆炸甚至不收敛。如何应对这些硬件故障、及时识别并分类，是提升集群节点的在线率与整体利用率的关键问题。 |

| 英文 | 中文 |
|------|------|
| Table V: Type of GPU Xid Errors and Its Causes | 表 V：GPU Xid 错误类型及其成因 |

**英文表**

| Xid Errors | Analysis |
| --- | --- |
| SoftwareCauses:Xid_13/31Xid_43/45 | Triggered by application programs, software-relatedXid messages may indicate anomalies in GPUmemory affecting code and data segments. However,it's crucial to consider other information for acomprehensive hardware functionality assessment. |
| NVLink Error:Xid 74 | Xid74 indicates errors in NVLink. For PCIe A100, it'smainly occurred on the NVLink Bridge between twoGPUs. Its occurrence rate is several orders ofmagnitude higher than other hardware faults. Apartfrom stress testing to exclude those that are constantlyrepeating errors, there isn't a good way to avoid theoccurrence of Xid74 issues. |
| MemoryECC Error:Xid_63/64Xid_94/95 | Triggered when the GPU handles memory ECC errorson the GPU. With the introduction of row remappingtechnology in A100, most instances can be resolvedby simply resetting the GPU to retain optimalperformance. |
| UncorrectableGPU Failures:Xid_44/48Xid_61/62/69/79 | Thease failures mean an uncorrectable error occurs onthe GPU, which is also reported back to the userapplication. A GPU reset or node reboot is needed toclear this error. |
| Other Failures:Xid 119 | Xid119 means GPU GSP module failed. These failuresneed to do fieldiag test, and most need to RMA. |

**中文表**

| Xid 错误 | 分析 |
|---|---|
| 软件原因：Xid_13/31、Xid_43/45 | 由应用程序触发。与软件相关的 Xid 消息可能表明 GPU 内存异常，影响代码段与数据段。然而，进行全面的硬件功能评估时，必须结合其他信息综合考虑。 |
| NVLink 错误：Xid 74 | Xid74 表示 NVLink 出现错误。对于 PCIe A100，它主要发生在两块 GPU 之间的 NVLink 桥上。其发生频率比其他硬件故障高出几个数量级。除了通过压力测试排除那些持续重复的错误外，没有好的办法避免 Xid74 问题的发生。 |
| 内存 ECC 错误：Xid_63/64、Xid_94/95 | 当 GPU 处理内存 ECC 错误时触发。随着 A100 引入行重映射（row remapping）技术，大多数情况只需重置 GPU 即可恢复最佳性能。 |
| 不可纠正的 GPU 故障：Xid_44/48、Xid_61/62/69/79 | 这些故障意味着 GPU 上发生了不可纠正的错误，也会上报给用户应用程序。需要重置 GPU 或重启节点才能清除此错误。 |
| 其他故障：Xid 119 | Xid119 表示 GPU GSP 模块故障。这些故障需要做现场诊断测试，多数需要 RMA 处理。 |

| 英文 | 中文 |
|------|------|
| 1) GPU Xid Error: An Xid error [88] is a general GPU fault message that originates from the NVIDIA driver, logged into the kernel or event log of the operating system. We have categorized various types of Xid errors and analyzed the potential causes that may lead to such errors, as shown in the Table V. | 1) GPU Xid 错误：Xid 错误 [88] 是源自 NVIDIA 驱动的通用 GPU 故障消息，会记录到操作系统的内核或事件日志中。我们对各种类型的 Xid 错误进行了分类，并分析了可能导致这些错误的潜在原因，如表 V 所示。 |

| 英文 | 中文 |
|------|------|
| Table VI in Appendix: Supplementary Characterization shows the Xid errors that have occurred in our Fire-Flyer 2 AI-HPC over the past year. In our PCIe-based system, Xid74, also known as NVLink errors, account for a significant proportion, comprising 42.57% of the total. This high frequency is due to the inherent fault rate of NVLink Bridge connectors, amplified by our extensive use of thousands of GPUs. | 附录中的表 VI（补充特征）展示了我们 Fire-Flyer 2 AI-HPC 过去一年中出现的 Xid 错误。在我们基于 PCIe 的系统中，Xid74（即 NVLink 错误）占比显著，占总数量的 42.57%。如此高的频率源于 NVLink 桥连接器固有的故障率，再加上我们数千块 GPU 的大规模使用而被放大。 |

| 英文 | 中文 |
|------|------|
| Software-related errors such as Xid13, Xid31, Xid43, and Xid45 suggest possible illegal memory access or instructions in user code. Notably, illegal memory access (Xid 43) accounts for 33.48%, highlighting the need for improved memory management. However, these errors may also result from memory data corruption, so hardware faults should be considered if software bugs are ruled out. | 软件相关的错误，如 Xid13、Xid31、Xid43 和 Xid45，暗示用户代码中可能存在非法内存访问或非法指令。值得注意的是，非法内存访问（Xid 43）占 33.48%，凸显了改进内存管理的必要性。然而，这些错误也可能源于内存数据损坏，因此在排除软件缺陷后，应考虑硬件故障的可能性。 |

| 英文 | 中文 |
|------|------|
| Additionally, GPU Memory ECC Errors, such as Xid63, Xid64, Xid94, and Xid95, require special attention as they represent about 2% of the total. Figure 10 illustrates the statistics related to ECC errors in our production cluster over the past six months. It is evident that the number of GPU ECC faults considerably surpasses those from the CPU. Therefore, it is crucial to promptly address GPU ECC faults to ensure that application performance and accuracy remain unaffected. | 此外，GPU 内存 ECC 错误（如 Xid63、Xid64、Xid94 和 Xid95）需要特别关注，因为它们约占总数的 2%。图 10 展示了我们生产集群过去六个月中与 ECC 错误相关的统计数据。显而易见，GPU ECC 故障的数量远超 CPU。因此，及时处理 GPU ECC 故障至关重要，以确保应用性能与精度不受影响。 |

| 英文 | 中文 |
|------|------|
| 2) Network Flash Cut: In addition to CPU and GPU faults, network device malfunctions represent a significant portion of hardware issues. As shown in Figure10, IB link failures account for 30% of hardware faults excluding Xid74. Network flash cuts can lead to application communication disruption, even task failures. Since most tasks run on multiple nodes, an issue on a single node can impact many others, further reducing cluster utilization. Figure 11 illustrates the IB link failures data over the past year, with raw data attached in Appendix: Supplementary Characterization, Table VIII, indicating that these issues can occur randomly throughout the cluster's operational period. | 2) 网络闪断：除 CPU 和 GPU 故障外，网络设备故障也是硬件问题的重要部分。如图 10 所示，IB 链路故障占除 Xid74 外硬件故障的 30%。网络闪断可能导致应用通信中断，甚至任务失败。由于大多数任务运行在多个节点上，单个节点的问题可能影响许多其他节点，进一步降低集群利用率。图 11 展示了过去一年的 IB 链路故障数据，原始数据附在附录：补充特征的表 VIII 中，表明这些问题可能在集群运行期间的任意时刻随机发生。 |

| 英文 | 中文 |
|------|------|
| ![](images/fb6886c6b8949cec32d3af3eafad9f9732b3b98bb63e2e53453312b18880d14e.jpg)   Figure 10: Trends of Memory and Network Failures from 2023 to 2024: “Main Memory" indicates CPU Memory ECC errors, “Network" indicates Network Flash Cuts, and “xids" are related to GPU memory ECC errors. Raw data is available in Appendix: Supplementary Characterization, Table VII | ![](images/fb6886c6b8949cec32d3af3eafad9f9732b3b98bb63e2e53453312b18880d14e.jpg) 图 10：2023 至 2024 年内存与网络故障趋势："主内存（Main Memory）"表示 CPU 内存 ECC 错误，"网络（Network）"表示网络闪断，"xids"与 GPU 内存 ECC 错误相关。原始数据见附录：补充特征的表 VII。 |

| 英文 | 中文 |
|------|------|
| ![](images/717ba9a8f47836d7d11641a0d21e1a60bf0c853e6ec87793e2e9c4e822bcbd6a.jpg)   Figure 11: Trends of IB Network Failures: Link Flash Cuts | ![](images/717ba9a8f47836d7d11641a0d21e1a60bf0c853e6ec87793e2e9c4e822bcbd6a.jpg) 图 11：IB 网络故障趋势：链路闪断。 |

## VIII. 讨论

## A. 关于 RDMA 网络拥塞控制的讨论（A. Discussion on Congestion Control in RDMA Networks）

| 英文 | 中文 |
|------|------|
| Lossless RDMA networks offer several flow-control mechanisms, such as Priority Flow Control (PFC) [89] for RoCE networks and credit-based flow control [90] for IB networks. In network routing, static routing algorithms in IB or ECMP (Equal-Cost Multi-Path) [91] and AR (Adaptive Routing) [92] effectively handle routing issues. However, congestion can still occur when multiple servers send data to a single receiver, potentially blocking the entire network. To mitigate this, IB NICs use DCQCN (Data Center Quantized Congestion Notification) [93] as their congestion control algorithm. While Data Processing Units (DPUs), such as the NVIDIA BF series, allow users to customize congestion control algorithms (like HPCC [94] and TIMELY RTT-based CC [95]), they increase the cost and operational complexity of the cluster. | 无损 RDMA 网络提供多种流控机制，如针对 RoCE 网络的优先级流控（Priority Flow Control, PFC）[89] 和针对 IB 网络的基于信用的流控 [90]。在网络路由方面，IB 中的静态路由算法或 ECMP（等价多路径）[91] 和 AR（自适应路由）[92] 能有效处理路由问题。然而，当多台服务器同时向单个接收方发送数据时，仍可能发生拥塞，甚至阻塞整个网络。为缓解这一问题，IB 网卡使用 DCQCN（数据中心量化拥塞通知）[93] 作为拥塞控制算法。虽然数据处理单元（Data Processing Unit, DPU）（如 NVIDIA BF 系列）允许用户自定义拥塞控制算法（如 HPCC [94] 和基于 TIMELY RTT 的拥塞控制 [95]），但它们会增加集群的成本与运维复杂度。 |

| 英文 | 中文 |
|------|------|
| In practice, we chose to disable DCQCN to avoid its shortcomings, as it could not find parameters that simultaneously support HFReduce traffic and 3FS storage traffic in our Computation-Storage Integrated Network. Instead, we employed the network tuning methods mentioned in Section VI-A, ensuring our network operates without congestion control and remains congestion-free. | 在实践中，我们选择禁用 DCQCN 以避免其缺陷——在我们的计算存储一体化网络中，我们找不到能同时支持 HFReduce 流量与 3FS 存储流量的参数。取而代之，我们采用了第六节-A 中提到的网络调优方法，确保我们的网络在无拥塞控制的情况下运行且保持无拥塞。 |

## B. 关于 NVLink 技术选型的讨论（B. Discussion about NVLink Technology Choices）

| 英文 | 中文 |
|------|------|
| Initially, we did not use NVLink to avoid extra costs and maintain stability, as HFReduce was sufficient for training requirements at that time. However, as the demand for LLMs increased, we added NVLink specifically for LLM training purposes. The decision to install NVLink should be based on actual needs due to its potential drawbacks. | 最初，我们为了节省额外成本并保持稳定性而不用 NVLink，因为当时 HFReduce 已足以满足训练需求。然而，随着对 LLM 需求的增加，我们专门为 LLM 训练加入了 NVLink。是否安装 NVLink 应根据实际需求来决定，因为它存在潜在弊端。 |

## C. 维护成本概览

| 英文 | 中文 |
|------|------|
| 1) Construction Cost: Relative hardware costs are provided in Table II and III. Software costs, contributed by several dozen in-house developers, are just a fraction of the cost for thousands of GPU servers. | 1) 建设成本：相对硬件成本见表 II 和 III。软件成本由数十名内部开发人员贡献，仅仅是数千台 GPU 服务器成本的一小部分。 |

| 英文 | 中文 |
|------|------|
| 2) Power Consumption: The average power consumption comparision during ResNet training is provided in Table II. Including the overhead from IB switches and other nodes, the total energy consumption of the Fire-Flyer 2 AI-HPC does not exceed 4 MW, approximately just over 3 MW. | 2) 功耗：ResNet 训练期间的平均功耗对比见表 II。算上 IB 交换机和其他节点的开销，Fire-Flyer 2 AI-HPC 的总能耗不超过 4 MW，大约略高于 3 MW。 |

| 英文 | 中文 |
|------|------|
| 3) Operation Cost: Operating costs can be estimated by considering power consumption and rack rental costs. By multiplying this figure by the number of nodes and the PUE (Power Usage Effectiveness), the total operating costs can be calculated. | 3) 运营成本：运营成本可通过考虑功耗与机架租赁成本来估算。将该数值乘以节点数和 PUE（电源使用效率），即可算出总运营成本。 |

## D. 与其他架构相比的稳定性

| 英文 | 中文 |
|------|------|
| A recent paper [96] reportsthat NVLink-related failures account for approximately 52.42% (54 out of 103) of total failures, with raw data indicating 54 NVLink Errors, 21 CUDA Errors, 16 Node Failures, 12 ECC Errors, and 12 Network Errors. In comparison, our NVLink-related issues, primarily Xid-74 Errors, as mentioned in Section VII-C1, account for about 42.57% of GPU failures. | 最近一篇论文 [96] 报告，NVLink 相关故障约占总故障的 52.42%（103 例中 54 例），原始数据显示有 54 例 NVLink 错误、21 例 CUDA 错误、16 例节点故障、12 例 ECC 错误和 12 例网络错误。相比之下，我们与 NVLink 相关的问题（主要是 Xid-74 错误，如第七节-C1 所述）约占 GPU 故障的 42.57%。 |

## IX. 未来工作

## 未来架构及与新 GPU 型号的集成

| 英文 | 中文 |
|------|------|
| Our next-generation PCIe architecture is designed for MoE (Mixture of Experts) LLM training, where all-to-all performance is crucial. Therefore, the next-gen nodes feature a 1:1 GPU to NIC ratio, comparable to DGX-H100/B100 systems, as illustrated in Figure 12. | 我们的下一代 PCIe 架构专为 MoE（混合专家）LLM 训练而设计，其中全对全性能至关重要。因此，下一代节点采用 1:1 的 GPU 与网卡配比，与 DGX-H100/B100 系统相当，如图 12 所示。 |

| 英文 | 中文 |
|------|------|
| We are considering implementing a multi-plane network to reduce costs while maintaining performance. Additionally, we are exploring the use of RoCE switches instead of IB switches, which can significantly lower network expenses. With a 128- port 400 Gbps RoCE switch, a 4-Plane Two-Layer Fat-Trees network can support up to 32,768 GPUs. | 我们正在考虑实现多平面网络，以在保持性能的同时降低成本。此外，我们正在探索使用 RoCE 交换机替代 IB 交换机，这能显著降低网络开销。采用 128 端口 400Gbps 的 RoCE 交换机，一个 4 平面两层胖树网络可支持多达 32,768 块 GPU。 |

| 英文 | 中文 |
|------|------|
| ![](images/23937960ce9eea36f9445f1844bdd925a2c87a36926c79476a39b9506a0fe97e.jpg)   Figure 12: Next Generation PCIe Node Atchitecture with Multi-Plane Fat-Trees Network | ![](images/23937960ce9eea36f9445f1844bdd925a2c87a36926c79476a39b9506a0fe97e.jpg) 图 12：采用多平面胖树网络的下一代 PCIe 节点架构。 |

## X. 结论

| 英文 | 中文 |
|------|------|
| In this paper, we have shared our experiences and insights from deploying and maintaining the Fire-Flyer 2 AI-HPC, which is equipped with 10,000 PCIe A100 GPUs.Our approach to PCIe architecture and storage-computation integrated network design has resulted in significant cost savings, effectively halving construction costs and demonstrating substantial cost-effectiveness. | 在本文中，我们分享了部署与维护配备 10,000 块 PCIe A100 GPU 的 Fire-Flyer 2 AI-HPC 的经验与见解。我们在 PCIe 架构与存储计算一体化网络设计上的方法带来了显著的成本节省，有效将建设成本减半，展现出可观的成本效益。 |

| 英文 | 中文 |
|------|------|
| In terms of software co-design, we introduced HFReduce and HaiScale to overcome hardware limitations, ensuring scalable performance of the PCIe architecture. Our in-house developed 3FS distributed file system,in conjunction with network co-design, facilitates traffic isolation for both 3FS and HFReduce allreduce traffic, effectively preventing congestion. The comprehensive software stack within the HAI Platform addresses a variety of system faults, from network congestion to hardware failures, thereby ensuring high stability and robustness. | 在软件协同设计方面，我们引入了 HFReduce 和 HaiScale 来克服硬件局限，确保 PCIe 架构的可扩展性能。我们自研的 3FS 分布式文件系统与网络协同设计相结合，为 3FS 与 HFReduce 的 allreduce 流量实现了流量隔离，有效防止拥塞。HAI 平台内全面的软件栈处理了从网络拥塞到硬件故障的各种系统问题，从而确保了高稳定性与鲁棒性。 |

| 英文 | 中文 |
|------|------|
| Together, these software and hardware innovations enable our PCIe A100 architecture to achieve 80% the performance of NVIDIA's DGX-A100, while consuming less than 60% of its power. The practical knowledge we have accrued may prove valuable for both industrial and academic sectors. We hope that our work will serve as a reference for others aiming to build their own cost-effective and efficient AI-HPC clusters. | 总而言之，这些软硬件创新使我们的 PCIe A100 架构实现了 NVIDIA DGX-A100 80% 的性能，而功耗不到其 60%。我们所积累的实践知识对工业界和学术界都可能具有价值。我们希望我们的工作能为那些希望构建自己高性价比、高效 AI-HPC 集群的人提供参考。 |

## 致谢（ACKNOWLEDGMENT）

| 英文 | 中文 |
|------|------|
| We extend our heartfelt gratitude to all our colleagues at DeepSeek-AI and High-Flyer Quant for their invaluable contributions to the Fire-Flyer 2 AI-HPC project. Throughout the four years of design, construction, and operation, their collaborative efforts have been crucial in overcoming numerous challenges. Consequently, Fire-Flyer 2 AI-HPC now supports the training tasks of the DeepSeek-AI series large language models [72], [97]-[101]. We extend a special thanks to the HFAiLab System Team and the Operations Team, whose core contributions have been essential to the success of this endeavor. | 我们衷心感谢 DeepSeek-AI 和幻方量化（High-Flyer Quant）的所有同事对 Fire-Flyer 2 AI-HPC 项目的宝贵贡献。在长达四年的设计、建设与运行过程中，他们的协作努力在克服无数挑战中至关重要。如今，Fire-Flyer 2 AI-HPC 支撑着 DeepSeek-AI 系列大语言模型 [72]、[97]–[101] 的训练任务。我们特别感谢 HFAiLab 系统团队与运维团队，他们的核心贡献对这一事业的成功不可或缺。 |

## REFERENCES

| 英文 | 中文 |
|------|------|
| [1] Y. LeCun, Y. Bengio, and G. Hinton, "Deep learning," nature, vol. 521, no. 7553, pp. 436–444, 2015. I | [1] Y. LeCun, Y. Bengio, and G. Hinton, "Deep learning," nature, vol. 521, no. 7553, pp. 436鈥?44, 2015. I |

| 英文 | 中文 |
|------|------|
| [2] R. R. Schaller, "Moore's law: past, present and future," IEEE spectrum, vol. 34, no. 6, pp. 52–59, 1997. I | [2] R. R. Schaller, "Moore's law: past, present and future," IEEE spectrum, vol. 34, no. 6, pp. 52鈥?9, 1997. I |

| 英文 | 中文 |
|------|------|
| [3] T. Brown, B. Mann, N. Ryder, M. Subbiah, J. D. Kaplan, P. Dhariwal, A. Neelakantan, P. Shyam, G. Sastry, A. Askell et al., "Language models are few-shot learners," Advances in neural information processing systems, vol. 33, pp. 1877–1901, 2020. I | [3] T. Brown, B. Mann, N. Ryder, M. Subbiah, J. D. Kaplan, P. Dhariwal, A. Neelakantan, P. Shyam, G. Sastry, A. Askell et al., "Language models are few-shot learners," Advances in neural information processing systems, vol. 33, pp. 1877鈥?901, 2020. I |

| 英文 | 中文 |
|------|------|
| [4] Anthropic, "Introducing claude," 2023. [Online]. Available: https: //www.anthropic.com/news/introducing-claude I | [4] Anthropic, "Introducing claude," 2023. [Online]. Available: https://www.anthropic.com/news/introducing-claude I |

| 英文 | 中文 |
|------|------|
| [5] Google, “An important next step on our ai journey," 2023. [Online]. Available: https://blog.google/technology/ai/bard-google-aisearch-updates/ I | [5] Google, 鈥淎n important next step on our ai journey," 2023. [Online]. Available: https://blog.google/technology/ai/bard-google-aisearch-updates/ I |

| 英文 | 中文 |
|------|------|
| [6] OpenAI, “Chatgpt: Optimizing language models for dialogue," 2022. [Online]. Available: https://openai.com/blog/chatgpt I | [6] OpenAI, 鈥淐hatgpt: Optimizing language models for dialogue," 2022. [Online]. Available: https://openai.com/blog/chatgpt I |

| 英文 | 中文 |
|------|------|
| [7] J. Achiam, S. Adler, S. Agarwal, L. Ahmad, I. Akkaya, F. L. Aleman, D. Almeida, J. Altenschmidt, S. Altman, S. Anadkat et al., "Gpt-4 technical report," arXiv preprint arXiv:2303.08774, 2023. I, II-A | [7] J. Achiam, S. Adler, S. Agarwal, L. Ahmad, I. Akkaya, F. L. Aleman, D. Almeida, J. Altenschmidt, S. Altman, S. Anadkat et al., "Gpt-4 technical report," arXiv preprint arXiv:2303.08774, 2023. I, II-A |

| 英文 | 中文 |
|------|------|
| [8] NVIDIA, “Nvidia dgx platform the best of nvidia ai—all in one place."2022. [Online]. Available: https://www.nvidia.com/en-us/datacenter/dgx-platform/ I, III-C | [8] NVIDIA, 鈥淣vidia dgx platform the best of nvidia ai鈥攁ll in one place."2022. [Online]. Available: https://www.nvidia.com/en-us/datacenter/dgx-platform/ I, III-C |

| 英文 | 中文 |
|------|------|
| [9] C. E. Leiserson, “Fat-trees: Universal networks for hardware-efficient supercomputing," IEEE Transactions on Computers, vol. C-34, no. 10, pp. 892–901, Oct 1985. I, III-B | [9] C. E. Leiserson, 鈥淔at-trees: Universal networks for hardware-efficient supercomputing," IEEE Transactions on Computers, vol. C-34, no. 10, pp. 892鈥?01, Oct 1985. I, III-B |

| 英文 | 中文 |
|------|------|
| [10] NVIDIA, “"Nvidia collective communications library (nccl): Optimized primitives for collective multi-gpu communication," 2017. [Online]. Available: https://github.com/NVIDIA/nccl I, III-B | [10] NVIDIA, 鈥?Nvidia collective communications library (nccl): Optimized primitives for collective multi-gpu communication," 2017. [Online]. Available: https://github.com/NVIDIA/nccl I, III-B |

| 英文 | 中文 |
|------|------|
| [11] Y. Huang, Y. Cheng, D. Chen, H. Lee, J. Ngiam, Q. V. Le, and Z. Chen, “"Gpipe: Efficient training of giant neural networks using pipeline parallelism," CoRR, vol. abs/1811.06965, 2018. [Online]. Available: http://arxiv.org/abs/1811.06965 I, II-B1, V-B | [11] Y. Huang, Y. Cheng, D. Chen, H. Lee, J. Ngiam, Q. V. Le, and Z. Chen, 鈥?Gpipe: Efficient training of giant neural networks using pipeline parallelism," CoRR, vol. abs/1811.06965, 2018. [Online]. Available: http://arxiv.org/abs/1811.06965 I, II-B1, V-B |

| 英文 | 中文 |
|------|------|
| [12] D. Narayanan, A. Harlap, A. Phanishayee, V. Seshadri, N. R. Devanur, G. R. Ganger, P. B. Gibbons, and M. Zaharia, "Pipedream: generalized pipeline parallelism for dnn training," in Proceedings of the 27th ACM Symposium on Operating Systems Principles, ser. SOSP '19. New York, NY, USA: Association for Computing Machinery, 2019, p. 1–15. [Online]. Available: https://doi.org/10.1145/3341301.3359646 I, II-B1, V-B | [12] D. Narayanan, A. Harlap, A. Phanishayee, V. Seshadri, N. R. Devanur, G. R. Ganger, P. B. Gibbons, and M. Zaharia, "Pipedream: generalized pipeline parallelism for dnn training," in Proceedings of the 27th ACM Symposium on Operating Systems Principles, ser. SOSP '19. New York, NY, USA: Association for Computing Machinery, 2019, p. 1鈥?5. [Online]. Available: https://doi.org/10.1145/3341301.3359646 I, II-B1, V-B |

| 英文 | 中文 |
|------|------|
| [13] M. Shoeybi, M. Patwary, R. Puri, P. LeGresley, J. Casper, and B. Catanzaro, "Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism,"Mar. 2020, arXiv:1909.08053 [cs]. [Online]. Available: http://arxiv.org/abs/1909.08053 I, II-B1 | [13] M. Shoeybi, M. Patwary, R. Puri, P. LeGresley, J. Casper, and B. Catanzaro, "Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism,"Mar. 2020, arXiv:1909.08053 [cs]. [Online]. Available: http://arxiv.org/abs/1909.08053 I, II-B1 |

| 英文 | 中文 |
|------|------|
| [14] D. Narayanan, M. Shoeybi, J. Casper, P. LeGresley, M. Patwary, V. Korthikanti, D. Vainbrand, P. Kashinkunti, J. Bernauer, B. Catanzaro, A. Phanishayee, and M. Zaharia, "Efficient large-scale language model training on gpu clusters using megatron-lm," in Proceedings of the International Conference for High Performance Computing, Networking, Storage and Analysis, ser. SC '21. New York, NY, USA: Association for Computing Machinery, 2021. [Online]. Available: https://doi.org/10.1145/3458817.3476209I, II-B1, V-B | [14] D. Narayanan, M. Shoeybi, J. Casper, P. LeGresley, M. Patwary, V. Korthikanti, D. Vainbrand, P. Kashinkunti, J. Bernauer, B. Catanzaro, A. Phanishayee, and M. Zaharia, "Efficient large-scale language model training on gpu clusters using megatron-lm," in Proceedings of the International Conference for High Performance Computing, Networking, Storage and Analysis, ser. SC '21. New York, NY, USA: Association for Computing Machinery, 2021. [Online]. Available: https://doi.org/10.1145/3458817.3476209I, II-B1, V-B |

| 英文 | 中文 |
|------|------|
| [15] S. Singh, O. Ruwase, A. A. Awan, S. Rajbhandari, Y. He, and A. Bhatele, “A hybrid tensor-expert-data parallelism approach to optimize mixture-of-experts training," in Proceedings of the 37th ACM International Conference on Supercomputing, ser. ICS '23. New York, NY, USA: Association for Computing Machinery, 2023, p. 203–214. [Online]. Available: https://doi.org/10.1145/3577193.3593704 I, II-B1, V-B | [15] S. Singh, O. Ruwase, A. A. Awan, S. Rajbhandari, Y. He, and A. Bhatele, 鈥淎 hybrid tensor-expert-data parallelism approach to optimize mixture-of-experts training," in Proceedings of the 37th ACM International Conference on Supercomputing, ser. ICS '23. New York, NY, USA: Association for Computing Machinery, 2023, p. 203鈥?14. [Online]. Available: https://doi.org/10.1145/3577193.3593704 I, II-B1, V-B |

| 英文 | 中文 |
|------|------|
| [16] S. Rajbhandari, C. Li, Z. Yao, M. Zhang, R. Aminabadi, A. Awan, J. Rasley, and Y. He, "Deepspeed-moe: Advancing mixture-of-experts inference and training to power next-generation ai scale," Proceedings of Machine Learning Research, vol. 162, pp. 18 332–18 346, 2022, publisher Copyright: Copyright © 2022 by the author(s); 39th International Conference on Machine Learning, ICML 2022 ; Conference date: 17- 07-2022 Through 23-07-2022. I, II-B1, V-B | [16] S. Rajbhandari, C. Li, Z. Yao, M. Zhang, R. Aminabadi, A. Awan, J. Rasley, and Y. He, "Deepspeed-moe: Advancing mixture-of-experts inference and training to power next-generation ai scale," Proceedings of Machine Learning Research, vol. 162, pp. 18 332鈥?8 346, 2022, publisher Copyright: Copyright 漏 2022 by the author(s); 39th International Conference on Machine Learning, ICML 2022 ; Conference date: 17- 07-2022 Through 23-07-2022. I, II-B1, V-B |

| 英文 | 中文 |
|------|------|
| [17] C. Hwang, W. Cui, Y. Xiong, Z. Yang, Z. Liu, H. Hu, Z. Wang, R. Salas, J. Jose, P. Ram et al., "Tutel: Adaptive mixture-of-experts at scale," Proceedings of Machine Learning and Systems, vol. 5, 2023. I, II-B1, V-B | [17] C. Hwang, W. Cui, Y. Xiong, Z. Yang, Z. Liu, H. Hu, Z. Wang, R. Salas, J. Jose, P. Ram et al., "Tutel: Adaptive mixture-of-experts at scale," Proceedings of Machine Learning and Systems, vol. 5, 2023. I, II-B1, V-B |

| 英文 | 中文 |
|------|------|
| [18] Y. Zhao, A. Gu, R. Varma, L. Luo, C.-C. Huang, M. Xu, L. Wright, H. Shojanazeri, M. Ott, S. Shleifer et al., "Pytorch fsdp: experiences on scaling fully sharded data parallel," arXiv preprint arXiv:2304.11277, 2023. I, V-B3 | [18] Y. Zhao, A. Gu, R. Varma, L. Luo, C.-C. Huang, M. Xu, L. Wright, H. Shojanazeri, M. Ott, S. Shleifer et al., "Pytorch fsdp: experiences on scaling fully sharded data parallel," arXiv preprint arXiv:2304.11277, 2023. I, V-B3 |

| 英文 | 中文 |
|------|------|
| [19] S. Rajbhandari, J. Rasley, O. Ruwase, and Y. He, "Zero: Memory optimizations toward training trillion parameter models," in SC20: International Conference for High Performance Computing, Networking, Storage and Analysis. IEEE, 2020, pp. 1–16. I, II-B1, II-B1, V-B3 | [19] S. Rajbhandari, J. Rasley, O. Ruwase, and Y. He, "Zero: Memory optimizations toward training trillion parameter models," in SC20: International Conference for High Performance Computing, Networking, Storage and Analysis. IEEE, 2020, pp. 1鈥?6. I, II-B1, II-B1, V-B3 |

| 英文 | 中文 |
|------|------|
| [20] HFAiLab, "Hai platform: A high-performance deep learning training platform with task-level gpu compute time-sharing scheduling," 2023. [Online]. Available: https://github.com/HFAiLab/hai-platform I | [20] HFAiLab, "Hai platform: A high-performance deep learning training platform with task-level gpu compute time-sharing scheduling," 2023. [Online]. Available: https://github.com/HFAiLab/hai-platform I |

| 英文 | 中文 |
|------|------|
| [21] A. Krizhevsky, I. Sutskever, and G. E. Hinton, "Imagenet classification with deep convolutional neural networks," Advances in neural information processing systems, vol. 25, 2012. II-A | [21] A. Krizhevsky, I. Sutskever, and G. E. Hinton, "Imagenet classification with deep convolutional neural networks," Advances in neural information processing systems, vol. 25, 2012. II-A |

| 英文 | 中文 |
|------|------|
| [22] K. He, X. Zhang, S. Ren, and J. Sun, "Deep residual learning for image recognition," in Proceedings of the IEEE conference on computer vision and pattern recognition, 2016, pp. 770–778. II-A, III | [22] K. He, X. Zhang, S. Ren, and J. Sun, "Deep residual learning for image recognition," in Proceedings of the IEEE conference on computer vision and pattern recognition, 2016, pp. 770鈥?78. II-A, III |

| 英文 | 中文 |
|------|------|
| [23] A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, Ł. Kaiser, and I. Polosukhin, "Attention is all you need," Advances in neural information processing systems, vol. 30, 2017. II-A | [23] A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, 艁. Kaiser, and I. Polosukhin, "Attention is all you need," Advances in neural information processing systems, vol. 30, 2017. II-A |

| 英文 | 中文 |
|------|------|
| [24] A. W. Senior, R. Evans, J. Jumper, J. Kirkpatrick, L. Sifre, T. Green, C. Qin, A. Žídek, A. W. Nelson, A. Bridgland et al., "Improved protein structure prediction using potentials from deep learning," Nature, vol. 577, no. 7792, pp. 706–710, 2020. II-A | [24] A. W. Senior, R. Evans, J. Jumper, J. Kirkpatrick, L. Sifre, T. Green, C. Qin, A. 沤铆dek, A. W. Nelson, A. Bridgland et al., "Improved protein structure prediction using potentials from deep learning," Nature, vol. 577, no. 7792, pp. 706鈥?10, 2020. II-A |

| 英文 | 中文 |
|------|------|
| [25] D. Silver, T. Hubert, J. Schrittwieser, I. Antonoglou, M. Lai, A. Guez, M. Lanctot, L. Sifre, D. Kumaran, T. Graepel et al., “A general reinforcement learning algorithm that masters chess, shogi, and go through self-play," Science, vol. 362, no. 6419, pp. 1140–1144, 2018. II-A | [25] D. Silver, T. Hubert, J. Schrittwieser, I. Antonoglou, M. Lai, A. Guez, M. Lanctot, L. Sifre, D. Kumaran, T. Graepel et al., 鈥淎 general reinforcement learning algorithm that masters chess, shogi, and go through self-play," Science, vol. 362, no. 6419, pp. 1140鈥?144, 2018. II-A |

| 英文 | 中文 |
|------|------|
| [26] L. Floridi and M. Chiriatti, "Gpt-3: Its nature, scope, limits, and consequences," Minds and Machines, vol. 30, pp. 681–694, 2020. II-A | [26] L. Floridi and M. Chiriatti, "Gpt-3: Its nature, scope, limits, and consequences," Minds and Machines, vol. 30, pp. 681鈥?94, 2020. II-A |

| 英文 | 中文 |
|------|------|
| [27] A. Chowdhery, S. Narang, J. Devlin, M. Bosma, G. Mishra, A. Roberts, P. Barham, H. W. Chung, C. Sutton, S. Gehrmann et al., "Palm: Scaling language modeling with pathways," Journal of Machine Learning Research, vol. 24, no. 240, pp. 1–113, 2023. II-A | [27] A. Chowdhery, S. Narang, J. Devlin, M. Bosma, G. Mishra, A. Roberts, P. Barham, H. W. Chung, C. Sutton, S. Gehrmann et al., "Palm: Scaling language modeling with pathways," Journal of Machine Learning Research, vol. 24, no. 240, pp. 1鈥?13, 2023. II-A |

| 英文 | 中文 |
|------|------|
| [28] R. A. Jacobs, M. I. Jordan, S. J. Nowlan, and G. E. Hinton, "Adaptive mixtures of local experts," Neural computation, vol. 3, no. 1, pp. 79–87, 1991. II-A | [28] R. A. Jacobs, M. I. Jordan, S. J. Nowlan, and G. E. Hinton, "Adaptive mixtures of local experts," Neural computation, vol. 3, no. 1, pp. 79鈥?7, 1991. II-A |

| 英文 | 中文 |
|------|------|
| [29] M. I. Jordan and R. A. Jacobs, "Hierarchical mixtures of experts and the em algorithm," Neural computation, vol. 6, no. 2, pp. 181–214, 1994. II-A | [29] M. I. Jordan and R. A. Jacobs, "Hierarchical mixtures of experts and the em algorithm," Neural computation, vol. 6, no. 2, pp. 181鈥?14, 1994. II-A |

| 英文 | 中文 |
|------|------|
| [30] N. Shazeer, A. Mirhoseini, K. Maziarz, A. Davis, Q. Le, G. Hinton, and J. Dean, "Outrageously large neural networks: The sparsely-gated mixture-of-experts layer," arXiv preprint arXiv:1701.06538, 2017. II-A | [30] N. Shazeer, A. Mirhoseini, K. Maziarz, A. Davis, Q. Le, G. Hinton, and J. Dean, "Outrageously large neural networks: The sparsely-gated mixture-of-experts layer," arXiv preprint arXiv:1701.06538, 2017. II-A |

| 英文 | 中文 |
|------|------|
| [31] T. Brooks, B. Peebles, C. Holmes, W. DePue, Y. Guo, L. Jing, D. Schnurr, J. Taylor, T. Luhman, E. Luhman, C. Ng, R. Wang, and A. Ramesh, “Video generation models as world simulators," 2024. [Online]. Available: https://openai.com/research/video-generation-modelsas-world-simulators II-A | [31] T. Brooks, B. Peebles, C. Holmes, W. DePue, Y. Guo, L. Jing, D. Schnurr, J. Taylor, T. Luhman, E. Luhman, C. Ng, R. Wang, and A. Ramesh, 鈥淰ideo generation models as world simulators," 2024. [Online]. Available: https://openai.com/research/video-generation-modelsas-world-simulators II-A |

| 英文 | 中文 |
|------|------|
| [32] A. Gholami, Z. Yao, S. Kim, C. Hooper, M. W. Mahoney, and K. Keutzer, “AI and Memory Wall," Mar. 2024, arXiv:2403.14123 [cs]. [Online]. Available: http://arxiv.org/abs/2403.14123 II-A | [32] A. Gholami, Z. Yao, S. Kim, C. Hooper, M. W. Mahoney, and K. Keutzer, 鈥淎I and Memory Wall," Mar. 2024, arXiv:2403.14123 [cs]. [Online]. Available: http://arxiv.org/abs/2403.14123 II-A |

| 英文 | 中文 |
|------|------|
| [33] P. Qi, X. Wan, G. Huang, and M. Lin, "Zero bubble pipeline parallelism," arXiv preprint arXiv:2401.10241, 2023. II-B1 | [33] P. Qi, X. Wan, G. Huang, and M. Lin, "Zero bubble pipeline parallelism," arXiv preprint arXiv:2401.10241, 2023. II-B1 |

| 英文 | 中文 |
|------|------|
| [34] V. A. Korthikanti, J. Casper, S. Lym, L. McAfee, M. Andersch, M. Shoeybi, and B. Catanzaro, "Reducing activation recomputation in large transformer models," in Proceedings of the Sixth Conference on Machine Learning and Systems, MLSys 2023, Miami, FL, USA, June 4-8, 2023, D. Song, M. Carbin, and T. C. 0001, Eds. mlsys.org, 2023. [Online]. Available: https://proceedings.mlsys.org/paper\_files/paper/2023/ hash/80083951326cf5b35e5100260d64ed81-Abstract-mlsys2023.html II-B1 | [34] V. A. Korthikanti, J. Casper, S. Lym, L. McAfee, M. Andersch, M. Shoeybi, and B. Catanzaro, "Reducing activation recomputation in large transformer models," in Proceedings of the Sixth Conference on Machine Learning and Systems, MLSys 2023, Miami, FL, USA, June 4-8, 2023, D. Song, M. Carbin, and T. C. 0001, Eds. mlsys.org, 2023. [Online]. Available: https://proceedings.mlsys.org/paper\_files/paper/2023/ hash/80083951326cf5b35e5100260d64ed81-Abstract-mlsys2023.html II-B1 |

| 英文 | 中文 |
|------|------|
| [35] Z. Sun, H. Cao, Y. Wang, G. Feng, S. Chen, H. Wang, and W. Chen, "Adapipe: Optimizing pipeline parallelism with adaptive recomputation and partitioning," in Proceedings of the 29th ACM International Conference on Architectural Support for Programming Languages and Operating Systems, Volume 3, ser. ASPLOS '24. New York, NY, USA: Association for Computing Machinery, 2024, p. 86–100. [Online]. Available: https://doi.org/10.1145/3620666.3651359 II-B1 | [35] Z. Sun, H. Cao, Y. Wang, G. Feng, S. Chen, H. Wang, and W. Chen, "Adapipe: Optimizing pipeline parallelism with adaptive recomputation and partitioning," in Proceedings of the 29th ACM International Conference on Architectural Support for Programming Languages and Operating Systems, Volume 3, ser. ASPLOS '24. New York, NY, USA: Association for Computing Machinery, 2024, p. 86鈥?00. [Online]. Available: https://doi.org/10.1145/3620666.3651359 II-B1 |

| 英文 | 中文 |
|------|------|
| [36] X. Hou, Y. Yuan, S. Ma, R. Xu, B. Wang, T. Li, W. Jiang, L. Wu, and J. Zhang, "Optimizing the parallelism of communication and computation in distributed training platform," in Algorithms and Architectures for Parallel Processing: 23rd International Conference, ICA3PP 2023, Tianjin, China, October 20–22, 2023, Proceedings, Part I. Berlin, Heidelberg: Springer-Verlag, 2024, p. 340–359. [Online]. Available: https://doi.org/10.1007/978-981-97-0834-5\_20II-B1 | [36] X. Hou, Y. Yuan, S. Ma, R. Xu, B. Wang, T. Li, W. Jiang, L. Wu, and J. Zhang, "Optimizing the parallelism of communication and computation in distributed training platform," in Algorithms and Architectures for Parallel Processing: 23rd International Conference, ICA3PP 2023, Tianjin, China, October 20鈥?2, 2023, Proceedings, Part I. Berlin, Heidelberg: Springer-Verlag, 2024, p. 340鈥?59. [Online]. Available: https://doi.org/10.1007/978-981-97-0834-5\_20II-B1 |

| 英文 | 中文 |
|------|------|
| [37] J. Dongarra, "REPORT ON THE TIANHE-2A SYSTEM," 2017. II-C1 | [37] J. Dongarra, "REPORT ON THE TIANHE-2A SYSTEM," 2017. II-C1 |

| 英文 | 中文 |
|------|------|
| [38] D. Stanzione, B. Barth, N. Gaffney, K. Gaither, C. Hempel, T. Minyard, S. Mehringer, E. Wernert, H. Tufo, D. Panda, and P. Teller, “Stampede 2: The evolution of an xsede supercomputer," in Proceedings of the Practice and Experience in Advanced Research Computing 2017 on Sustainability, Success and Impact, ser. PEARC '17. New York, NY, USA: Association for Computing Machinery, 2017. [Online]. Available: https://doi.org/10.1145/3093338.3093385 II-C1 | [38] D. Stanzione, B. Barth, N. Gaffney, K. Gaither, C. Hempel, T. Minyard, S. Mehringer, E. Wernert, H. Tufo, D. Panda, and P. Teller, 鈥淪tampede 2: The evolution of an xsede supercomputer," in Proceedings of the Practice and Experience in Advanced Research Computing 2017 on Sustainability, Success and Impact, ser. PEARC '17. New York, NY, USA: Association for Computing Machinery, 2017. [Online]. Available: https://doi.org/10.1145/3093338.3093385 II-C1 |

| 英文 | 中文 |
|------|------|
| [39] H. Fu, J. Liao, J. Yang, L. Wang, Z. Song, X. Huang, C. Yang, W. Xue, F. Liu, F. Qiao, W. Zhao, X. Yin, C. Hou, C. Zhang, W. Ge, J. Zhang, Y. Wang, C. Zhou, and G. Yang, "The Sunway TaihuLight supercomputer: system and applications," Science China Information Sciences, vol. 59, no. 7, p. 072001, Jul. 2016. [Online]. Available: http://link.springer.com/10.1007/s11432-016-5588-7 II-C1 | [39] H. Fu, J. Liao, J. Yang, L. Wang, Z. Song, X. Huang, C. Yang, W. Xue, F. Liu, F. Qiao, W. Zhao, X. Yin, C. Hou, C. Zhang, W. Ge, J. Zhang, Y. Wang, C. Zhou, and G. Yang, "The Sunway TaihuLight supercomputer: system and applications," Science China Information Sciences, vol. 59, no. 7, p. 072001, Jul. 2016. [Online]. Available: http://link.springer.com/10.1007/s11432-016-5588-7 II-C1 |

| 英文 | 中文 |
|------|------|
| [40] T. Shimizu, "Supercomputer Fugaku: Co-designed with application developers/researchers," in 2020 IEEE Asian Solid-State Circuits Conference (A-SSCC). Hiroshima, Japan: IEEE, Nov. 2020, pp. 1– 4. [Online]. Available: https://ieeexplore.ieee.org/document/9336127/ II-C1 | [40] T. Shimizu, "Supercomputer Fugaku: Co-designed with application developers/researchers," in 2020 IEEE Asian Solid-State Circuits Conference (A-SSCC). Hiroshima, Japan: IEEE, Nov. 2020, pp. 1鈥?4. [Online]. Available: https://ieeexplore.ieee.org/document/9336127/ II-C1 |

| 英文 | 中文 |
|------|------|
| [41] D. Schneider, “The Exascale Era is Upon Us: The Frontier supercomputer may be the first to reach 1,000,000,000,000,000,000 operations per second," IEEE Spectrum, vol. 59, no. 1, pp. 34–35, Jan. 2022. [Online]. Available: https://ieeexplore.ieee.org/document/ 9676353/II-C2 | [41] D. Schneider, 鈥淭he Exascale Era is Upon Us: The Frontier supercomputer may be the first to reach 1,000,000,000,000,000,000 operations per second," IEEE Spectrum, vol. 59, no. 1, pp. 34鈥?5, Jan. 2022. [Online]. Available: https://ieeexplore.ieee.org/document/ 9676353/II-C2 |

| 英文 | 中文 |
|------|------|
| [42] A. N. Laboratory, “Argonne's aurora supercomputer," 2023. [Online]. Available: https://www.alcf.anl.gov/aurora II-C2 | [42] A. N. Laboratory, 鈥淎rgonne's aurora supercomputer," 2023. [Online]. Available: https://www.alcf.anl.gov/aurora II-C2 |

| 英文 | 中文 |
|------|------|
| [43] C. B. Stunkel, R. L. Graham, G. Shainer, M. Kagan, S. S. Sharkawi, B. Rosenburg, and G. A. Chochia, "The high-speed networks of the Summit and Sierra supercomputers," IBM Journal of Research and Development, vol. 64, no. 3/4, pp. 3:1–3:10, May 2020. [Online]. Available: https://ieeexplore.ieee.org/document/8961159/II-C2 | [43] C. B. Stunkel, R. L. Graham, G. Shainer, M. Kagan, S. S. Sharkawi, B. Rosenburg, and G. A. Chochia, "The high-speed networks of the Summit and Sierra supercomputers," IBM Journal of Research and Development, vol. 64, no. 3/4, pp. 3:1鈥?:10, May 2020. [Online]. Available: https://ieeexplore.ieee.org/document/8961159/II-C2 |

| 英文 | 中文 |
|------|------|
| [44] J. Gu, G. Eisenhauer, S. Klasky, N. Podhorszki, R. Wang, and K. Wu, “Exploring large all-flash storage system with scientific simulation," in Proceedings of the 34th International Conference on Scientific and Statistical Database Management, ser. SSDBM '22. New York, NY, USA: Association for Computing Machinery, 2022. [Online]. Available: https://doi.org/10.1145/3538712.3538734II-C2 | [44] J. Gu, G. Eisenhauer, S. Klasky, N. Podhorszki, R. Wang, and K. Wu, 鈥淓xploring large all-flash storage system with scientific simulation," in Proceedings of the 34th International Conference on Scientific and Statistical Database Management, ser. SSDBM '22. New York, NY, USA: Association for Computing Machinery, 2022. [Online]. Available: https://doi.org/10.1145/3538712.3538734II-C2 |

| 英文 | 中文 |
|------|------|
| [45] D. Mudigere, Y. Hao, J. Huang, Z. Jia, A. Tulloch, S. Sridharan, X. Liu, M. Ozdal, J. Nie, J. Park, L. Luo, J. A. Yang, L. Gao, D. Ivchenko, A. Basant, Y. Hu, J. Yang, E. K. Ardestani, X. Wang, R. Komuravelli, C.-H. Chu, S. Yilmaz, H. Li, J. Qian, Z. Feng, Y. Ma, J. Yang, E. Wen, H. Li, L. Yang, C. Sun, W. Zhao, D. Melts, K. Dhulipala, K. R. Kishore, T. Graf, A. Eisenman, K. K. Matam, A. Gangidi, G. J. Chen, M. Krishnan, A. Nayak, K. Nair, B. Muthiah, M. khorashadi, P. Bhattacharya, P. Lapukhov, M. Naumov, A. Mathews, L. Qiao, M. Smelyanskiy, B. Jia, and V. Rao, “Software-Hardware Co-design for Fast and Scalable Training of Deep Learning Recommendation Models," Feb. 2023, arXiv:2104.05158 [cs]. [Online]. Available: http://arxiv.org/abs/2104.05158 II-C3 | [45] D. Mudigere, Y. Hao, J. Huang, Z. Jia, A. Tulloch, S. Sridharan, X. Liu, M. Ozdal, J. Nie, J. Park, L. Luo, J. A. Yang, L. Gao, D. Ivchenko, A. Basant, Y. Hu, J. Yang, E. K. Ardestani, X. Wang, R. Komuravelli, C.-H. Chu, S. Yilmaz, H. Li, J. Qian, Z. Feng, Y. Ma, J. Yang, E. Wen, H. Li, L. Yang, C. Sun, W. Zhao, D. Melts, K. Dhulipala, K. R. Kishore, T. Graf, A. Eisenman, K. K. Matam, A. Gangidi, G. J. Chen, M. Krishnan, A. Nayak, K. Nair, B. Muthiah, M. khorashadi, P. Bhattacharya, P. Lapukhov, M. Naumov, A. Mathews, L. Qiao, M. Smelyanskiy, B. Jia, and V. Rao, 鈥淪oftware-Hardware Co-design for Fast and Scalable Training of Deep Learning Recommendation Models," Feb. 2023, arXiv:2104.05158 [cs]. [Online]. Available: http://arxiv.org/abs/2104.05158 II-C3 |

| 英文 | 中文 |
|------|------|
| [46] A. Gangidi, R. Miao, S. Zheng, S. J. Bondu, G. Goes, H. Morsy, R. Puri, M. Riftadi, A. J. Shetty, J. Yang, S. Zhang, M. J. Fernandez, S. Gandham, and H. Zeng, "Rdma over ethernet for distributed training at meta scale," in Proceedings of the ACM SIGCOMM 2024 Conference, ser. ACM SIGCOMM '24. New York, NY, USA: Association for Computing Machinery, 2024, p. 57–70. [Online]. Available: https://doi.org/10.1145/3651890.3672233 II-C3 | [46] A. Gangidi, R. Miao, S. Zheng, S. J. Bondu, G. Goes, H. Morsy, R. Puri, M. Riftadi, A. J. Shetty, J. Yang, S. Zhang, M. J. Fernandez, S. Gandham, and H. Zeng, "Rdma over ethernet for distributed training at meta scale," in Proceedings of the ACM SIGCOMM 2024 Conference, ser. ACM SIGCOMM '24. New York, NY, USA: Association for Computing Machinery, 2024, p. 57鈥?0. [Online]. Available: https://doi.org/10.1145/3651890.3672233 II-C3 |

| 英文 | 中文 |
|------|------|
| [47] Y. Jiang, Y. Zhu, C. Lan, B. Yi, Y. Cui, and C. Guo, "A Unified Architecture for Accelerating Distributed DNN Training in Heterogeneous GPU/CPU Clusters." II-C3 | [47] Y. Jiang, Y. Zhu, C. Lan, B. Yi, Y. Cui, and C. Guo, "A Unified Architecture for Accelerating Distributed DNN Training in Heterogeneous GPU/CPU Clusters." II-C3 |

| 英文 | 中文 |
|------|------|
| [48] Z. Jiang, H. Lin, Y. Zhong, Q. Huang, Y. Chen, Z. Zhang, Y. Peng, X. Li, C. Xie, S. Nong, Y. Jia, S. He, H. Chen, Z. Bai, Q. Hou, S. Yan, D. Zhou, Y. Sheng, Z. Jiang, H. Xu, H. Wei, Z. Zhang, P. Nie, L. Zou, S. Zhao, L. Xiang, Z. Liu, Z. Li, X. Jia, J. Ye, X. Jin, and X. Liu, "MegaScale: Scaling Large Language Model Training to More Than 10,000 GPUs," Feb. 2024, arXiv:2402.15627 [cs]. [Online]. Available: http://arxiv.org/abs/2402.15627 II-C3 | [48] Z. Jiang, H. Lin, Y. Zhong, Q. Huang, Y. Chen, Z. Zhang, Y. Peng, X. Li, C. Xie, S. Nong, Y. Jia, S. He, H. Chen, Z. Bai, Q. Hou, S. Yan, D. Zhou, Y. Sheng, Z. Jiang, H. Xu, H. Wei, Z. Zhang, P. Nie, L. Zou, S. Zhao, L. Xiang, Z. Liu, Z. Li, X. Jia, J. Ye, X. Jin, and X. Liu, "MegaScale: Scaling Large Language Model Training to More Than 10,000 GPUs," Feb. 2024, arXiv:2402.15627 [cs]. [Online]. Available: http://arxiv.org/abs/2402.15627 II-C3 |

| 英文 | 中文 |
|------|------|
| [49] K. Qian, Y. Xi, J. Cao, J. Gao, Y. Xu, Y. Guan, B. Fu, X. Shi, F. Zhu, R. Miao, C. Wang, P. Wang, P. Zhang, X. Zeng, E. Ruan, Z. Yao, E. Zhai, and D. Cai, “Alibaba hpn: A data center network for large language model training," in Proceedings of the ACM SIGCOMM 2024 Conference, ser. ACM SIGCOMM '24. New York, NY, USA: Association for Computing Machinery, 2024, p. 691–706. [Online]. Available: https://doi.org/10.1145/3651890.3672265 II-C3 | [49] K. Qian, Y. Xi, J. Cao, J. Gao, Y. Xu, Y. Guan, B. Fu, X. Shi, F. Zhu, R. Miao, C. Wang, P. Wang, P. Zhang, X. Zeng, E. Ruan, Z. Yao, E. Zhai, and D. Cai, 鈥淎libaba hpn: A data center network for large language model training," in Proceedings of the ACM SIGCOMM 2024 Conference, ser. ACM SIGCOMM '24. New York, NY, USA: Association for Computing Machinery, 2024, p. 691鈥?06. [Online]. Available: https://doi.org/10.1145/3651890.3672265 II-C3 |

| 英文 | 中文 |
|------|------|
| [50] NVIDIA, “Nvidia announces dgx h100 systems - world's most advanced enterprise ai infrastructure," 2023. [Online]. Available: https://nvidianews.nvidia.com/news/nvidia-announces-dgx-h100- systems-worlds-most-advanced-enterprise-ai-infrastructure II-C3 | [50] NVIDIA, 鈥淣vidia announces dgx h100 systems - world's most advanced enterprise ai infrastructure," 2023. [Online]. Available: https://nvidianews.nvidia.com/news/nvidia-announces-dgx-h100- systems-worlds-most-advanced-enterprise-ai-infrastructure II-C3 |

| 英文 | 中文 |
|------|------|
| [51] N. Jouppi, G. Kurian, S. Li, P. Ma, R. Nagarajan, L. Nai, N. Patil, S. Subramanian, A. Swing, B. Towles, C. Young, X. Zhou, Z. Zhou, and D. A. Patterson, "TPU v4: An Optically Reconfigurable Supercomputer for Machine Learning with Hardware Support for Embeddings," in Proceedings of the 50th Annual International Symposium on Computer Architecture. Orlando FL USA: ACM, Jun. 2023, pp. 1–14. [Online]. Available: https://dl.acm.org/doi/10.1145/3579371.3589350 II-C4 | [51] N. Jouppi, G. Kurian, S. Li, P. Ma, R. Nagarajan, L. Nai, N. Patil, S. Subramanian, A. Swing, B. Towles, C. Young, X. Zhou, Z. Zhou, and D. A. Patterson, "TPU v4: An Optically Reconfigurable Supercomputer for Machine Learning with Hardware Support for Embeddings," in Proceedings of the 50th Annual International Symposium on Computer Architecture. Orlando FL USA: ACM, Jun. 2023, pp. 1鈥?4. [Online]. Available: https://dl.acm.org/doi/10.1145/3579371.3589350 II-C4 |

| 英文 | 中文 |
|------|------|
| [52] C. Zhang, B. Sun, X. Yu, Z. Xie, W. Zheng, K. Iskra, P. Beckman, and D. Tao, "Benchmarking and In-depth Performance Study of Large Language Models on Habana Gaudi Processors," Sep. 2023, arXiv:2309.16976 [cs]. [Online]. Available: http://arxiv.org/abs/ 2309.16976 II-C4 | [52] C. Zhang, B. Sun, X. Yu, Z. Xie, W. Zheng, K. Iskra, P. Beckman, and D. Tao, "Benchmarking and In-depth Performance Study of Large Language Models on Habana Gaudi Processors," Sep. 2023, arXiv:2309.16976 [cs]. [Online]. Available: http://arxiv.org/abs/ 2309.16976 II-C4 |

| 英文 | 中文 |
|------|------|
| [53] E. Talpes, D. Williams, and D. D. Sarma, "Dojo: The microarchitecture of tesla's exa-scale computer," in 2022 IEEE Hot Chips 34 Symposium (HCS), 2022, pp. 1–28. II-C4 | [53] E. Talpes, D. Williams, and D. D. Sarma, "Dojo: The microarchitecture of tesla's exa-scale computer," in 2022 IEEE Hot Chips 34 Symposium (HCS), 2022, pp. 1鈥?8. II-C4 |

| 英文 | 中文 |
|------|------|
| [54] E. Talpes, D. D. Sarma, D. Williams, S. Arora, T. Kunjan, B. Floering, A. Jalote, C. Hsiong, C. Poorna, V. Samant, J. Sicilia, A. K. Nivarti, R. Ramachandran, T. Fischer, B. Herzberg, B. McGee, G. Venkataramanan, and P. Banon, "The microarchitecture of dojo, tesla's exa-scale computer," IEEE Micro, vol. 43, no. 3, pp. 31–39, 2023. II-C4 | [54] E. Talpes, D. D. Sarma, D. Williams, S. Arora, T. Kunjan, B. Floering, A. Jalote, C. Hsiong, C. Poorna, V. Samant, J. Sicilia, A. K. Nivarti, R. Ramachandran, T. Fischer, B. Herzberg, B. McGee, G. Venkataramanan, and P. Banon, "The microarchitecture of dojo, tesla's exa-scale computer," IEEE Micro, vol. 43, no. 3, pp. 31鈥?9, 2023. II-C4 |

| 英文 | 中文 |
|------|------|
| [55] H. Liao, J. Tu, J. Xia, and X. Zhou, "Davinci: A scalable architecture for neural network computing," in 2019 IEEE Hot Chips 31 Symposium (HCS), 2019, pp. 1–44. II-C4 | [55] H. Liao, J. Tu, J. Xia, and X. Zhou, "Davinci: A scalable architecture for neural network computing," in 2019 IEEE Hot Chips 31 Symposium (HCS), 2019, pp. 1鈥?4. II-C4 |

| 英文 | 中文 |
|------|------|
| [56] H. Liao, J. Tu, J. Xia, H. Liu, X. Zhou, H. Yuan, and Y. Hu, "Ascend: a scalable and unified architecture for ubiquitous deep neural network computing : Industry track paper," in 2021 IEEE International Symposium on High-Performance Computer Architecture (HPCA), 2021, pp. 789–801. II-C4 | [56] H. Liao, J. Tu, J. Xia, H. Liu, X. Zhou, H. Yuan, and Y. Hu, "Ascend: a scalable and unified architecture for ubiquitous deep neural network computing : Industry track paper," in 2021 IEEE International Symposium on High-Performance Computer Architecture (HPCA), 2021, pp. 789鈥?01. II-C4 |

| 英文 | 中文 |
|------|------|
| [57] D. Milojicic, P. Faraboschi, N. Dube, and D. Roweth, "Future of hpc: Diversifying heterogeneity," in 2021 Design, Automation Test in Europe Conference Exhibition (DATE), 2021, pp. 276–281. II-D | [57] D. Milojicic, P. Faraboschi, N. Dube, and D. Roweth, "Future of hpc: Diversifying heterogeneity," in 2021 Design, Automation Test in Europe Conference Exhibition (DATE), 2021, pp. 276鈥?81. II-D |

| 英文 | 中文 |
|------|------|
| [58] Y. Su, J. Zhou, J. Ying, M. Zhou, and B. Zhou, “Computing infrastructure construction and optimization for high-performance computing and artificial intelligence," CCF Transactions on High Performance Computing, vol. 3, no. 4, pp. 331–343, Dec. 2021. [Online]. Available: https://doi.org/10.1007/s42514-021-00080-x II-D | [58] Y. Su, J. Zhou, J. Ying, M. Zhou, and B. Zhou, 鈥淐omputing infrastructure construction and optimization for high-performance computing and artificial intelligence," CCF Transactions on High Performance Computing, vol. 3, no. 4, pp. 331鈥?43, Dec. 2021. [Online]. Available: https://doi.org/10.1007/s42514-021-00080-x II-D |

| 英文 | 中文 |
|------|------|
| [59] E. Hassan, N. El-Rashidy, and F. M. Talaa, “Review: Mask R-CNN Models," Nile Journal of Communication and Computer Science, vol. 3, no. 1, pp. 17–27, May 2022. [Online]. Available: https://njccs.journals.ekb.eg/article\_280047.html III | [59] E. Hassan, N. El-Rashidy, and F. M. Talaa, 鈥淩eview: Mask R-CNN Models," Nile Journal of Communication and Computer Science, vol. 3, no. 1, pp. 17鈥?7, May 2022. [Online]. Available: https://njccs.journals.ekb.eg/article\_280047.html III |

| 英文 | 中文 |
|------|------|
| [60] J. Devlin, M.-W. Chang, K. Lee, and K. Toutanova, "Bert: Pre-training of deep bidirectional transformers for language understanding," in North American Chapter of the Association for Computational Linguistics, 2019. [Online]. Available: https://api.semanticscholar.org/ CorpusID:52967399 III | [60] J. Devlin, M.-W. Chang, K. Lee, and K. Toutanova, "Bert: Pre-training of deep bidirectional transformers for language understanding," in North American Chapter of the Association for Computational Linguistics, 2019. [Online]. Available: https://api.semanticscholar.org/ CorpusID:52967399 III |

| 英文 | 中文 |
|------|------|
| [61] K. He, X. Chen, S. Xie, Y. Li, P. Dollár, and R. Girshick, "Masked autoencoders are scalable vision learners," arXiv:2111.06377, 2021. III | [61] K. He, X. Chen, S. Xie, Y. Li, P. Doll谩r, and R. Girshick, "Masked autoencoders are scalable vision learners," arXiv:2111.06377, 2021. III |

| 英文 | 中文 |
|------|------|
| [62] J. Kim, W. J. Dally, S. Scott, and D. Abts, "Technology-driven, highlyscalable dragonfly topology," in 2008 International Symposium on Computer Architecture, 2008, pp. 77–88. III-B | [62] J. Kim, W. J. Dally, S. Scott, and D. Abts, "Technology-driven, highlyscalable dragonfly topology," in 2008 International Symposium on Computer Architecture, 2008, pp. 77鈥?8. III-B |

| 英文 | 中文 |
|------|------|
| [63] G. Feng, D. Dong, and Y. Lu, "Optimized mpi collective algorithms for dragonfly topology," in Proceedings of the 36th ACM International Conference on Supercomputing, ser. ICS '22. New York, NY, USA: Association for Computing Machinery, 2022. [Online]. Available: https://doi.org/10.1145/3524059.3532380III-B | [63] G. Feng, D. Dong, and Y. Lu, "Optimized mpi collective algorithms for dragonfly topology," in Proceedings of the 36th ACM International Conference on Supercomputing, ser. ICS '22. New York, NY, USA: Association for Computing Machinery, 2022. [Online]. Available: https://doi.org/10.1145/3524059.3532380III-B |

| 英文 | 中文 |
|------|------|
| [64] H. Subramoni, P. Lai, M. Luo, and D. K. Panda, "Rdma over ethernet — a preliminary study," in 2009 IEEE International Conference on Cluster Computing and Workshops, 2009, pp. 1–9. III-B | [64] H. Subramoni, P. Lai, M. Luo, and D. K. Panda, "Rdma over ethernet 鈥?a preliminary study," in 2009 IEEE International Conference on Cluster Computing and Workshops, 2009, pp. 1鈥?. III-B |

| 英文 | 中文 |
|------|------|
| [65] P. Sanders, J. Speck, and J. Träff, “Two-tree algorithms for full bandwidth broadcast, reduction and scan," Parallel Computing, vol. 35, pp. 581–594, 12 2009. III-B, IV, 1, IV-D1 | [65] P. Sanders, J. Speck, and J. Tr盲ff, 鈥淭wo-tree algorithms for full bandwidth broadcast, reduction and scan," Parallel Computing, vol. 35, pp. 581鈥?94, 12 2009. III-B, IV, 1, IV-D1 |

| 英文 | 中文 |
|------|------|
| [66] R. Shi, S. Potluri, K. Hamidouche, J. Perkins, M. Li, D. Rossetti, and D. K. D. K. Panda, "Designing efficient small message transfer mechanism for inter-node mpi communication on infiniband gpu clusters," in 2014 21st International Conference on High Performance Computing (HiPC), 2014, pp. 1–10. 1 | [66] R. Shi, S. Potluri, K. Hamidouche, J. Perkins, M. Li, D. Rossetti, and D. K. D. K. Panda, "Designing efficient small message transfer mechanism for inter-node mpi communication on infiniband gpu clusters," in 2014 21st International Conference on High Performance Computing (HiPC), 2014, pp. 1鈥?0. 1 |

| 英文 | 中文 |
|------|------|
| [67] P. Foundation, “Tensors and dynamic neural networks in python with strong gpu acceleration," 2016. [Online]. Available: https: //github.com/pytorch/pytorch V-A | [67] P. Foundation, 鈥淭ensors and dynamic neural networks in python with strong gpu acceleration," 2016. [Online]. Available: https://github.com/pytorch/pytorch V-A |

| 英文 | 中文 |
|------|------|
| [68] S. Liu and W. Deng, "Very deep convolutional neural network based image classification using small training sample size," in 2015 3rd IAPR Asian Conference on Pattern Recognition (ACPR), 2015, pp. 730–734. V-A | [68] S. Liu and W. Deng, "Very deep convolutional neural network based image classification using small training sample size," in 2015 3rd IAPR Asian Conference on Pattern Recognition (ACPR), 2015, pp. 730鈥?34. V-A |

| 英文 | 中文 |
|------|------|
| [69] M. Shoeybi, M. Patwary, R. Puri, P. LeGresley, J. Casper, and B. Catanzaro, “Megatron-lm: Training multi-billion parameter language models using model parallelism," arXiv preprint arXiv:1909.08053, 2019. V-B | [69] M. Shoeybi, M. Patwary, R. Puri, P. LeGresley, J. Casper, and B. Catanzaro, 鈥淢egatron-lm: Training multi-billion parameter language models using model parallelism," arXiv preprint arXiv:1909.08053, 2019. V-B |

| 英文 | 中文 |
|------|------|
| [70] J. Rasley, S. Rajbhandari, O. Ruwase, and Y. He, "Deepspeed: System optimizations enable training deep learning models with over 100 billion parameters," in Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, ser. KDD '20. New York, NY, USA: Association for Computing Machinery, 2020, p. 3505–3506. [Online]. Available: https://doi.org/10.1145/3394486.3406703V-B | [70] J. Rasley, S. Rajbhandari, O. Ruwase, and Y. He, "Deepspeed: System optimizations enable training deep learning models with over 100 billion parameters," in Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, ser. KDD '20. New York, NY, USA: Association for Computing Machinery, 2020, p. 3505鈥?506. [Online]. Available: https://doi.org/10.1145/3394486.3406703V-B |

| 英文 | 中文 |
|------|------|
| [71] H. Touvron, T. Lavril, G. Izacard, X. Martinet, M.-A. Lachaux, T. Lacroix, B. Rozière, N. Goyal, E. Hambro, F. Azhar, A. Rodriguez A. Joulin, E. Grave, and G. Lample, "Llama: Open and efficient foundation language models," ArXiv, vol. abs/2302.13971, 2023. [Online]. Available: https://api.semanticscholar.org/CorpusID:257219404V-B2 | [71] H. Touvron, T. Lavril, G. Izacard, X. Martinet, M.-A. Lachaux, T. Lacroix, B. Rozi猫re, N. Goyal, E. Hambro, F. Azhar, A. Rodriguez A. Joulin, E. Grave, and G. Lample, "Llama: Open and efficient foundation language models," ArXiv, vol. abs/2302.13971, 2023. [Online]. Available: https://api.semanticscholar.org/CorpusID:257219404V-B2 |

| 英文 | 中文 |
|------|------|
| [72] DeepSeek-AI, A. Liu, B. Feng, B. Wang, B. Wang, B. Liu, C. Zhao, C. Dengr, C. Ruan, D. Dai, D. Guo, D. Yang, D. Chen, D. Ji, E. Li, F. Lin, F. Luo, G. Hao, G. Chen, G. Li, H. Zhang, H. Xu, H. Yang, H. Zhang, H. Ding, H. Xin, H. Gao, H. Li, H. Qu, J. L. Cai, J. Liang, J. Guo, J. Ni, J. Li, J. Chen, J. Yuan, J. Qiu, J. Song, K. Dong, K. Gao, K. Guan, L. Wang, L. Zhang, L. Xu, L. Xia, L. Zhao, L. Zhang, M. Li, M. Wang, M. Zhang, M. Zhang, M. Tang, M. Li, N. Tian, P. Huang, P. Wang, P. Zhang, Q. Zhu, Q. Chen, Q. Du, R. J. Chen, R. L. Jin, R. Ge, R. Pan, R. Xu, R. Chen, S. S. Li, S. Lu, S. Zhou, S. Chen, S. Wu, S. Ye, S. Ma, S. Wang, S. Zhou, S. Yu, S. Zhou, S. Zheng, T. Wang, T. Pei, T. Yuan, T. Sun, W. L. Xiao, W. Zeng, W. An, W. Liu, W. Liang, W. Gao, W. Zhang, X. Q. Li, X. Jin, X. Wang, X. Bi, X. Liu, X. Wang, X. Shen, X. Chen, X. Chen, X. Nie, X. Sun, X. Wang, X. Liu, X. Xie, X. Yu, X. Song, X. Zhou, X. Yang, X. Lu, X. Su, Y. Wu, Y. K. Li, Y. X. Wei, Y. X. Zhu, Y. Xu, Y. Huang, Y. Li, Y. Zhao, Y. Sun, Y. Li, Y. Wang, Y. Zheng, Y. Zhang, Y. Xiong, Y. Zhao, Y. He, Y. Tang, Y. Piao, Y. Dong, Y. Tan, Y. Liu, Y. Wang, Y. Guo, Y. Zhu, Y. Wang, Y. Zou, Y. Zha, Y. Ma, Y. Yan, Y. You, Y. Liu, Z. Z. Ren, Z. Ren, Z. Sha, Z. Fu, Z. Huang, Z. Zhang, Z. Xie, Z. Hao, Z. Shao, Z. Wen, Z. Xu, Z. Zhang, Z. Li, Z. Wang, Z. Gu, Z. Li, and Z. Xie, "DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model," Jun. 2024, arXiv:2405.04434 [cs]. [Online]. Available: http://arxiv.org/abs/2405.04434 V-B2, X | [72] DeepSeek-AI, A. Liu, B. Feng, B. Wang, B. Wang, B. Liu, C. Zhao, C. Dengr, C. Ruan, D. Dai, D. Guo, D. Yang, D. Chen, D. Ji, E. Li, F. Lin, F. Luo, G. Hao, G. Chen, G. Li, H. Zhang, H. Xu, H. Yang, H. Zhang, H. Ding, H. Xin, H. Gao, H. Li, H. Qu, J. L. Cai, J. Liang, J. Guo, J. Ni, J. Li, J. Chen, J. Yuan, J. Qiu, J. Song, K. Dong, K. Gao, K. Guan, L. Wang, L. Zhang, L. Xu, L. Xia, L. Zhao, L. Zhang, M. Li, M. Wang, M. Zhang, M. Zhang, M. Tang, M. Li, N. Tian, P. Huang, P. Wang, P. Zhang, Q. Zhu, Q. Chen, Q. Du, R. J. Chen, R. L. Jin, R. Ge, R. Pan, R. Xu, R. Chen, S. S. Li, S. Lu, S. Zhou, S. Chen, S. Wu, S. Ye, S. Ma, S. Wang, S. Zhou, S. Yu, S. Zhou, S. Zheng, T. Wang, T. Pei, T. Yuan, T. Sun, W. L. Xiao, W. Zeng, W. An, W. Liu, W. Liang, W. Gao, W. Zhang, X. Q. Li, X. Jin, X. Wang, X. Bi, X. Liu, X. Wang, X. Shen, X. Chen, X. Chen, X. Nie, X. Sun, X. Wang, X. Liu, X. Xie, X. Yu, X. Song, X. Zhou, X. Yang, X. Lu, X. Su, Y. Wu, Y. K. Li, Y. X. Wei, Y. X. Zhu, Y. Xu, Y. Huang, Y. Li, Y. Zhao, Y. Sun, Y. Li, Y. Wang, Y. Zheng, Y. Zhang, Y. Xiong, Y. Zhao, Y. He, Y. Tang, Y. Piao, Y. Dong, Y. Tan, Y. Liu, Y. Wang, Y. Guo, Y. Zhu, Y. Wang, Y. Zou, Y. Zha, Y. Ma, Y. Yan, Y. You, Y. Liu, Z. Z. Ren, Z. Ren, Z. Sha, Z. Fu, Z. Huang, Z. Zhang, Z. Xie, Z. Hao, Z. Shao, Z. Wen, Z. Xu, Z. Zhang, Z. Li, Z. Wang, Z. Gu, Z. Li, and Z. Xie, "DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model," Jun. 2024, arXiv:2405.04434 [cs]. [Online]. Available: http://arxiv.org/abs/2405.04434 V-B2, X |

| 英文 | 中文 |
|------|------|
| [73] A. Radford, J. Wu, R. Child, D. Luan, D. Amodei, and I. Sutskever, “Language models are unsupervised multitask learners," 2019. V-B3 | [73] A. Radford, J. Wu, R. Child, D. Luan, D. Amodei, and I. Sutskever, 鈥淟anguage models are unsupervised multitask learners," 2019. V-B3 |

| 英文 | 中文 |
|------|------|
| [74] S.-A. Reinemo, T. Skeie, T. Sodring, O. Lysne, and O. Trudbakken, “An overview of qos capabilities in infiniband, advanced switching interconnect, and ethernet," IEEE Communications Magazine, vol. 44, no. 7, pp. 32–38, 2006. VI-A1, VI-A1 | [74] S.-A. Reinemo, T. Skeie, T. Sodring, O. Lysne, and O. Trudbakken, 鈥淎n overview of qos capabilities in infiniband, advanced switching interconnect, and ethernet," IEEE Communications Magazine, vol. 44, no. 7, pp. 32鈥?8, 2006. VI-A1, VI-A1 |

| 英文 | 中文 |
|------|------|
| [75] D. Crupnicoff, S. Das, and E. Zahavi, “"Deploying Quality of Service and Congestion Control in InfiniBand-based Data Center Networks." [Online].Available:https://network.nvidia.com/sites/default/files/ related-docs/whitepapers/deploying\_qos\_wp\_10\_19\_2005.pdf VI-A1, VI-A1 | [75] D. Crupnicoff, S. Das, and E. Zahavi, 鈥?Deploying Quality of Service and Congestion Control in InfiniBand-based Data Center Networks." [Online].Available:https://network.nvidia.com/sites/default/files/ related-docs/whitepapers/deploying\_qos\_wp\_10\_19\_2005.pdf VI-A1, VI-A1 |

| 英文 | 中文 |
|------|------|
| [76] M. Scharf and S. Kiesel, “Nxg03-5: Head-of-line blocking in tcp and sctp: Analysis and measurements," in IEEE Globecom 2006, 2006, pp. 1–5. VI-A1 | [76] M. Scharf and S. Kiesel, 鈥淣xg03-5: Head-of-line blocking in tcp and sctp: Analysis and measurements," in IEEE Globecom 2006, 2006, pp. 1鈥?. VI-A1 |

| 英文 | 中文 |
|------|------|
| [77] R. Budruk, D. Anderson, and E. Solari, PCI Express System Architecture. Pearson Education, 2003. VI-A3 | [77] R. Budruk, D. Anderson, and E. Solari, PCI Express System Architecture. Pearson Education, 2003. VI-A3 |

| 英文 | 中文 |
|------|------|
| [78] Z. Liran, H. David, and M. Barbara, "Wekafs architecture white paper," 2021. [Online]. Available: https://www.weka.io/wp-content/uploads/files/2017/ 12/Architectural\_WhitePaper-W02R6WP201812-1.pdf VI-B1 | [78] Z. Liran, H. David, and M. Barbara, "Wekafs architecture white paper," 2021. [Online]. Available: https://www.weka.io/wp-content/uploads/files/2017/ 12/Architectural\_WhitePaper-W02R6WP201812-1.pdf VI-B1 |

| 英文 | 中文 |
|------|------|
| [79] Z. Liang, J. Lombardi, M. Chaarawi, and M. Hennecke, "Daos: A scale-out high performance storage stack for storage class memory," in Supercomputing Frontiers, D. K. Panda, Ed. Cham: Springer International Publishing, 2020, pp. 40–54. VI-B1 | [79] Z. Liang, J. Lombardi, M. Chaarawi, and M. Hennecke, "Daos: A scale-out high performance storage stack for storage class memory," in Supercomputing Frontiers, D. K. Panda, Ed. Cham: Springer International Publishing, 2020, pp. 40鈥?4. VI-B1 |

| 英文 | 中文 |
|------|------|
| [80] M. Hennecke, "Understanding daos storage performance scalability," in Proceedings of the HPC Asia 2023 Workshops, ser. HPCAsia '23 Workshops. New York, NY, USA: Association for Computing Machinery, 2023, p. 1–14. [Online]. Available: https://doi.org/10.1145/ 3581576.3581577VI-B1 | [80] M. Hennecke, "Understanding daos storage performance scalability," in Proceedings of the HPC Asia 2023 Workshops, ser. HPCAsia '23 Workshops. New York, NY, USA: Association for Computing Machinery, 2023, p. 1鈥?4. [Online]. Available: https://doi.org/10.1145/ 3581576.3581577VI-B1 |

| 英文 | 中文 |
|------|------|
| [81] H. Frank and B. Sven, "Wekafs architecture white paper," | [81] H. Frank and B. Sven, "Wekafs architecture white paper," |

| 英文 | 中文 |
|------|------|
| 2018. [Online]. Available: https://www.beegfs.io/docs/whitepapers/ Introduction\_to\_BeeGFS\_by\_ThinkParQ.pdf VI-B1 | 2018. [Online]. Available: https://www.beegfs.io/docs/whitepapers/ Introduction\_to\_BeeGFS\_by\_ThinkParQ.pdf VI-B1 |

| 英文 | 中文 |
|------|------|
| [82] J. Terrace and M. J. Freedman, "Object storage on CRAQ: High-Throughput chain replication for Read-Mostly workloads," in 2009 USENIX Annual Technical Conference (USENIX ATC 09). San Diego, CA: USENIX Association, Jun. 2009. [Online]. Available:https://www.usenix.org/conference/usenix-09/object-storagecraq-high-throughput-chain-replication-read-mostly-workloads VI-B3 | [82] J. Terrace and M. J. Freedman, "Object storage on CRAQ: High-Throughput chain replication for Read-Mostly workloads," in 2009 USENIX Annual Technical Conference (USENIX ATC 09). San Diego, CA: USENIX Association, Jun. 2009. [Online]. Available:https://www.usenix.org/conference/usenix-09/object-storagecraq-high-throughput-chain-replication-read-mostly-workloads VI-B3 |

| 英文 | 中文 |
|------|------|
| [83] E. B. Nightingale, J. Elson, J. Fan, O. Hofmann, J. Howell, and Y. Suzue, “Flat datacenter storage," in Proceedings of the 10th USENIX Conference on Operating Systems Design and Implementation, ser. OSDI'12. USA: USENIX Association, 2012, p. 1–15. VI-B3 | [83] E. B. Nightingale, J. Elson, J. Fan, O. Hofmann, J. Howell, and Y. Suzue, 鈥淔lat datacenter storage," in Proceedings of the 10th USENIX Conference on Operating Systems Design and Implementation, ser. OSDI'12. USA: USENIX Association, 2012, p. 1鈥?5. VI-B3 |

| 英文 | 中文 |
|------|------|
| [84] DeepSeek-AI, "Deepseek api introduces context caching on disk, cutting prices by an order of magnitude," 2024. [Online]. Available: https://platform.deepseek.com/api-docs/news/news0802 VI-B4 | [84] DeepSeek-AI, "Deepseek api introduces context caching on disk, cutting prices by an order of magnitude," 2024. [Online]. Available: https://platform.deepseek.com/api-docs/news/news0802 VI-B4 |

| 英文 | 中文 |
|------|------|
| [85] K. Liu, Z. Jiang, J. Zhang, H. Wei, X. Zhong, L. Tan, T. Pan, and T. Huang, "Hostping: Diagnosing intra-host network bottlenecks in RDMA servers," in 20th USENIX Symposium on Networked Systems Design and Implementation (NSDI 23). Boston, MA: USENIX Association, Apr. 2023, pp. 15-29. [Online]. Available: https://www.usenix.org/conference/nsdi23/presentation/liu-kefei VII-B | [85] K. Liu, Z. Jiang, J. Zhang, H. Wei, X. Zhong, L. Tan, T. Pan, and T. Huang, "Hostping: Diagnosing intra-host network bottlenecks in RDMA servers," in 20th USENIX Symposium on Networked Systems Design and Implementation (NSDI 23). Boston, MA: USENIX Association, Apr. 2023, pp. 15-29. [Online]. Available: https://www.usenix.org/conference/nsdi23/presentation/liu-kefei VII-B |

| 英文 | 中文 |
|------|------|
| [86] Y. He, M. Hutton, S. Chan, R. De Gruijl, R. Govindaraju, N. Patil, and Y. Li, "Understanding and Mitigating Hardware Failures in Deep Learning Training Systems," in Proceedings of the 50th Annual International Symposium on Computer Architecture. Orlando FL USA: ACM, Jun. 2023, pp. 1–16. [Online]. Available: https://dl.acm.org/doi/10.1145/3579371.3589105VII-C | [86] Y. He, M. Hutton, S. Chan, R. De Gruijl, R. Govindaraju, N. Patil, and Y. Li, "Understanding and Mitigating Hardware Failures in Deep Learning Training Systems," in Proceedings of the 50th Annual International Symposium on Computer Architecture. Orlando FL USA: ACM, Jun. 2023, pp. 1鈥?6. [Online]. Available: https://dl.acm.org/doi/10.1145/3579371.3589105VII-C |

| 英文 | 中文 |
|------|------|
| [87] S. Wang, G. Zhang, J. Wei, Y. Wang, J. Wu, and Q. Luo, "Understanding Silent Data Corruptions in a Large Production CPU Population," in Proceedings of the 29th Symposium on Operating Systems Principles. Koblenz Germany: ACM, Oct. 2023, pp. 216–230. [Online]. Available: https://dl.acm.org/doi/10.1145/3600006.3613149 VII-C | [87] S. Wang, G. Zhang, J. Wei, Y. Wang, J. Wu, and Q. Luo, "Understanding Silent Data Corruptions in a Large Production CPU Population," in Proceedings of the 29th Symposium on Operating Systems Principles. Koblenz Germany: ACM, Oct. 2023, pp. 216鈥?30. [Online]. Available: https://dl.acm.org/doi/10.1145/3600006.3613149 VII-C |

| 英文 | 中文 |
|------|------|
| [88] NVIDIA, “This document explains what xid messages are, and is intended to assist system administrators, developers, and faes in understanding the meaning behind these messages as an aid in analyzing and resolving gpu-related problems." [Online]. Available: https://docs.nvidia.com/deploy/xid-errors/VII-C1 | [88] NVIDIA, 鈥淭his document explains what xid messages are, and is intended to assist system administrators, developers, and faes in understanding the meaning behind these messages as an aid in analyzing and resolving gpu-related problems." [Online]. Available: https://docs.nvidia.com/deploy/xid-errors/VII-C1 |

| 英文 | 中文 |
|------|------|
| [89] "Priority flow control : Build reliable layer 2 infrastructure," 2015. [Online]. Available: https://api.semanticscholar.org/CorpusID: 42645413 VIII-A | [89] "Priority flow control : Build reliable layer 2 infrastructure," 2015. [Online]. Available: https://api.semanticscholar.org/CorpusID: 42645413 VIII-A |

| 英文 | 中文 |
|------|------|
| [90] S. Yan, G. Min, and I. Awan, "Performance analysis of creditbased flow control in infiniband interconnection networks," Journal of Interconnection Networks, vol. 07, no. 04, pp. 535–548, 2006. [Online]. Available: https://doi.org/10.1142/S0219265906001843 VIII-A | [90] S. Yan, G. Min, and I. Awan, "Performance analysis of creditbased flow control in infiniband interconnection networks," Journal of Interconnection Networks, vol. 07, no. 04, pp. 535鈥?48, 2006. [Online]. Available: https://doi.org/10.1142/S0219265906001843 VIII-A |

| 英文 | 中文 |
|------|------|
| [91] E. Nepolo and G.-A. Lusilao Zodi, “A predictive ecmp routing protocol for fat-tree enabled data centre networks," in 2021 15th International Conference on Ubiquitous Information Management and Communication (IMCOM), 2021, pp. 1–8. VIII-A | [91] E. Nepolo and G.-A. Lusilao Zodi, 鈥淎 predictive ecmp routing protocol for fat-tree enabled data centre networks," in 2021 15th International Conference on Ubiquitous Information Management and Communication (IMCOM), 2021, pp. 1鈥?. VIII-A |

| 英文 | 中文 |
|------|------|
| [92] J. Rocher-González, E. G. Gran, S.-A. Reinemo, T. Skeie, J. Escudero-Sahuquillo, P. J. García, and F. J. Q. Flor, "Adaptive routing in infiniband hardware," in 2022 22nd IEEE International Symposium on Cluster, Cloud and Internet Computing (CCGrid), 2022, pp. 463–472. VIII-A | [92] J. Rocher-Gonz谩lez, E. G. Gran, S.-A. Reinemo, T. Skeie, J. Escudero-Sahuquillo, P. J. Garc铆a, and F. J. Q. Flor, "Adaptive routing in infiniband hardware," in 2022 22nd IEEE International Symposium on Cluster, Cloud and Internet Computing (CCGrid), 2022, pp. 463鈥?72. VIII-A |

| 英文 | 中文 |
|------|------|
| [93] Y. Zhu, H. Eran, D. Firestone, C. Guo, M. Lipshteyn, Y. Liron, J. Padhye, S. Raindel, M. H. Yahia, and M. Zhang, "Congestion control for large-scale rdma deployments," SIGCOMM Comput. Commun. Rev., vol. 45, no. 4, p. 523–536, aug 2015. [Online]. Available: https://doi.org/10.1145/2829988.2787484 VIII-A | [93] Y. Zhu, H. Eran, D. Firestone, C. Guo, M. Lipshteyn, Y. Liron, J. Padhye, S. Raindel, M. H. Yahia, and M. Zhang, "Congestion control for large-scale rdma deployments," SIGCOMM Comput. Commun. Rev., vol. 45, no. 4, p. 523鈥?36, aug 2015. [Online]. Available: https://doi.org/10.1145/2829988.2787484 VIII-A |

| 英文 | 中文 |
|------|------|
| [94] Y. Li, R. Miao, H. H. Liu, Y. Zhuang, F. Feng, L. Tang, Z. Cao, M. Zhang, F. Kelly, M. Alizadeh, and M. Yu, "Hpcc: high precision congestion control," in Proceedings of the ACM Special Interest Group on Data Communication, ser. SIGCOMM '19. New York, NY, USA: Association for Computing Machinery, 2019, p. 44–58. [Online]. Available: https://doi.org/10.1145/3341302.3342085 VIII-A | [94] Y. Li, R. Miao, H. H. Liu, Y. Zhuang, F. Feng, L. Tang, Z. Cao, M. Zhang, F. Kelly, M. Alizadeh, and M. Yu, "Hpcc: high precision congestion control," in Proceedings of the ACM Special Interest Group on Data Communication, ser. SIGCOMM '19. New York, NY, USA: Association for Computing Machinery, 2019, p. 44鈥?8. [Online]. Available: https://doi.org/10.1145/3341302.3342085 VIII-A |

| 英文 | 中文 |
|------|------|
| [95] R. Mittal, V. T. Lam, N. Dukkipati, E. R. Blem, H. M. G. Wassel, M. Ghobadi, A. Vahdat, Y. Wang, D. Wetherall, and D. Zats, “Timely: Rtt-based congestion control for the datacenter," Proceedings of the 2015 ACM Conference on Special Interest Group on Data Communication, 2015. [Online]. Available: https: //api.semanticscholar.org/CorpusID:9676894 VIII-A | [95] R. Mittal, V. T. Lam, N. Dukkipati, E. R. Blem, H. M. G. Wassel, M. Ghobadi, A. Vahdat, Y. Wang, D. Wetherall, and D. Zats, 鈥淭imely: Rtt-based congestion control for the datacenter," Proceedings of the 2015 ACM Conference on Special Interest Group on Data Communication, 2015. [Online]. Available: https://api.semanticscholar.org/CorpusID:9676894 VIII-A |

| 英文 | 中文 |
|------|------|
| [96] Q. Hu, Z. Ye, Z. Wang, G. Wang, M. Zhang, Q. Chen, P. Sun, D. Lin, X. Wang, Y. Luo et al., "Characterization of large language model development in the datacenter," in 21st USENIX Symposium on Net- | [96] Q. Hu, Z. Ye, Z. Wang, G. Wang, M. Zhang, Q. Chen, P. Sun, D. Lin, X. Wang, Y. Luo et al., "Characterization of large language model development in the datacenter," in 21st USENIX Symposium on Net- |

| 英文 | 中文 |
|------|------|
| worked Systems Design and Implementation (NSDI 24), 2024, pp. 709– 729. VIII-D | worked Systems Design and Implementation (NSDI 24), 2024, pp. 709鈥?729. VIII-D |

| 英文 | 中文 |
|------|------|
| [97] DeepSeek-AI, X. Bi, D. Chen, G. Chen, S. Chen, D. Dai, C. Deng, H. Ding, K. Dong, Q. Du, Z. Fu, H. Gao, K. Gao, W. Gao, R. Ge, K. Guan, D. Guo, J. Guo, G. Hao, Z. Hao, Y. He, W. Hu, P. Huang, E. Li, G. Li, J. Li, Y. Li, Y. K. Li, W. Liang, F. Lin, A. X. Liu, B. Liu, W. Liu, X. Liu, X. Liu, Y. Liu, H. Lu, S. Lu, F. Luo, S. Ma, X. Nie, T. Pei, Y. Piao, J. Qiu, H. Qu, T. Ren, Z. Ren, C. Ruan, Z. Sha, Z. Shao, J. Song, X. Su, J. Sun, Y. Sun, M. Tang, B. Wang, P. Wang, S. Wang, Y. Wang, Y. Wang, T. Wu, Y. Wu, X. Xie, Z. Xie, Z. Xie, Y. Xiong, H. Xu, R. X. Xu, Y. Xu, D. Yang, Y. You, S. Yu, X. Yu, B. Zhang, H. Zhang, L. Zhang, L. Zhang, M. Zhang, M. Zhang, W. Zhang, Y. Zhang, C. Zhao, Y. Zhao, S. Zhou, S. Zhou, Q. Zhu, and Y. Zou, "DeepSeek LLM: Scaling Open-Source Language Models with Longtermism," Jan. 2024, arXiv:2401.02954 [cs]. [Online]. Available: http://arxiv.org/abs/2401.02954 X | [97] DeepSeek-AI, X. Bi, D. Chen, G. Chen, S. Chen, D. Dai, C. Deng, H. Ding, K. Dong, Q. Du, Z. Fu, H. Gao, K. Gao, W. Gao, R. Ge, K. Guan, D. Guo, J. Guo, G. Hao, Z. Hao, Y. He, W. Hu, P. Huang, E. Li, G. Li, J. Li, Y. Li, Y. K. Li, W. Liang, F. Lin, A. X. Liu, B. Liu, W. Liu, X. Liu, X. Liu, Y. Liu, H. Lu, S. Lu, F. Luo, S. Ma, X. Nie, T. Pei, Y. Piao, J. Qiu, H. Qu, T. Ren, Z. Ren, C. Ruan, Z. Sha, Z. Shao, J. Song, X. Su, J. Sun, Y. Sun, M. Tang, B. Wang, P. Wang, S. Wang, Y. Wang, Y. Wang, T. Wu, Y. Wu, X. Xie, Z. Xie, Z. Xie, Y. Xiong, H. Xu, R. X. Xu, Y. Xu, D. Yang, Y. You, S. Yu, X. Yu, B. Zhang, H. Zhang, L. Zhang, L. Zhang, M. Zhang, M. Zhang, W. Zhang, Y. Zhang, C. Zhao, Y. Zhao, S. Zhou, S. Zhou, Q. Zhu, and Y. Zou, "DeepSeek LLM: Scaling Open-Source Language Models with Longtermism," Jan. 2024, arXiv:2401.02954 [cs]. [Online]. Available: http://arxiv.org/abs/2401.02954 X |

| 英文 | 中文 |
|------|------|
| [98] Z. Shao, P. Wang, Q. Zhu, R. Xu, J. Song, X. Bi, H. Zhang, M. Zhang, Y. K. Li, Y. Wu, and D. Guo, "DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models," Apr. 2024, arXiv:2402.03300 [cs]. [Online]. Available: http://arxiv.org/abs/2402.03300X | [98] Z. Shao, P. Wang, Q. Zhu, R. Xu, J. Song, X. Bi, H. Zhang, M. Zhang, Y. K. Li, Y. Wu, and D. Guo, "DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models," Apr. 2024, arXiv:2402.03300 [cs]. [Online]. Available: http://arxiv.org/abs/2402.03300X |

| 英文 | 中文 |
|------|------|
| [99] H. Lu, W. Liu, B. Zhang, B. Wang, K. Dong, B. Liu, J. Sun, T. Ren, Z. Li, H. Yang, Y. Sun, C. Deng, H. Xu, Z. Xie, and C. Ruan, “DeepSeek-VL: Towards Real-World Vision-Language Understanding," Mar. 2024, arXiv:2403.05525 [cs]. [Online]. Available: http://arxiv.org/abs/2403.05525 X | [99] H. Lu, W. Liu, B. Zhang, B. Wang, K. Dong, B. Liu, J. Sun, T. Ren, Z. Li, H. Yang, Y. Sun, C. Deng, H. Xu, Z. Xie, and C. Ruan, 鈥淒eepSeek-VL: Towards Real-World Vision-Language Understanding," Mar. 2024, arXiv:2403.05525 [cs]. [Online]. Available: http://arxiv.org/abs/2403.05525 X |

| 英文 | 中文 |
|------|------|
| [100] DeepSeek-AI, Q. Zhu, D. Guo, Z. Shao, D. Yang, P. Wang, R. Xu, Y. Wu, Y. Li, H. Gao, S. Ma, W. Zeng, X. Bi, Z. Gu, H. Xu, D. Dai, K. Dong, L. Zhang, Y. Piao, Z. Gou, Z. Xie, Z. Hao, B. Wang, J. Song, D. Chen, X. Xie, K. Guan, Y. You, A. Liu, Q. Du, W. Gao, X. Lu, Q. Chen, Y. Wang, C. Deng, J. Li, C. Zhao, C. Ruan, F. Luo, and W. Liang, “DeepSeek-Coder-V2: Breaking the Barrier of Closed-Source Models in Code Intelligence," Jun. 2024, arXiv:2406.11931 [cs]. [Online]. Available: http://arxiv.org/abs/2406.11931 X | [100] DeepSeek-AI, Q. Zhu, D. Guo, Z. Shao, D. Yang, P. Wang, R. Xu, Y. Wu, Y. Li, H. Gao, S. Ma, W. Zeng, X. Bi, Z. Gu, H. Xu, D. Dai, K. Dong, L. Zhang, Y. Piao, Z. Gou, Z. Xie, Z. Hao, B. Wang, J. Song, D. Chen, X. Xie, K. Guan, Y. You, A. Liu, Q. Du, W. Gao, X. Lu, Q. Chen, Y. Wang, C. Deng, J. Li, C. Zhao, C. Ruan, F. Luo, and W. Liang, 鈥淒eepSeek-Coder-V2: Breaking the Barrier of Closed-Source Models in Code Intelligence," Jun. 2024, arXiv:2406.11931 [cs]. [Online]. Available: http://arxiv.org/abs/2406.11931 X |

| 英文 | 中文 |
|------|------|
| [101] H. Xin, Z. Z. Ren, J. Song, Z. Shao, W. Zhao, H. Wang, B. Liu, L. Zhang, X. Lu, Q. Du, W. Gao, Q. Zhu, D. Yang, Z. Gou, Z. F. Wu, F. Luo, and C. Ruan, "DeepSeek-Prover-V1.5: Harnessing Proof Assistant Feedback for Reinforcement Learning and Monte-Carlo Tree Search," Aug. 2024, arXiv:2408.08152 [cs]. [Online]. Available: http://arxiv.org/abs/2408.08152 X | [101] H. Xin, Z. Z. Ren, J. Song, Z. Shao, W. Zhao, H. Wang, B. Liu, L. Zhang, X. Lu, Q. Du, W. Gao, Q. Zhu, D. Yang, Z. Gou, Z. F. Wu, F. Luo, and C. Ruan, "DeepSeek-Prover-V1.5: Harnessing Proof Assistant Feedback for Reinforcement Learning and Monte-Carlo Tree Search," Aug. 2024, arXiv:2408.08152 [cs]. [Online]. Available: http://arxiv.org/abs/2408.08152 X |

| 英文 | 中文 |
|------|------|
| Table VI: Raw Data of GPU Xid Errors in Our Cluster Over the Past Year, as Mentioned in Section VII-C1 | 表 VI：我们集群过去一年 GPU Xid 错误的原始数据，见第七节-C1 |

**英文表**

| GPU Error Type | Xid Code | Number | Percentage |
| --- | --- | --- | --- |
| NVLink Error | xid_74 | 5521 | 42.57% |
| Software Causes | xid_13 | 45 | 0.35%19.18%33.48%1.85% |
|  | xid_31xid_43xid_45 | 24874342240 |
| GPU ECC Error | xid_63xid_64 | 2452 | 1.89%0.02%0.10%0.13% |
| xid_94 | 13 |
| xid_95 | 17 |
| Uncorrectable Failures | xid_44 | 1 | 0.01% |
|  | xid_48 | 2 | 0.02% |
| xid_61 | 13 | 0.10% |
| xid_62 | 3 | 0.02% |
| xid_69 | 1 | 0.01%0.29% |
| xid_79 | 37 |
| GPU GSP ERROR | xid_119 | 1 | 0.01% |
| Total |  | 12970 | 100.00% |

**中文表**

| GPU 错误类型 | Xid 代码 | 数量 | 百分比 |
|---|---|---|---|
| NVLink 错误 | xid_74 | 5521 | 42.57% |
| 软件原因 | xid_13 | 45 | 0.35% |
|  | xid_31 | 2487 | 19.18% |
|  | xid_43 | 4342 | 33.48% |
|  | xid_45 | 240 | 1.85% |
| GPU ECC 错误 | xid_63 | 2452 | 1.89% |
|  | xid_64 | 2 | 0.02% |
|  | xid_94 | 13 | 0.10% |
|  | xid_95 | 17 | 0.13% |
| 不可纠正的故障 | xid_44 | 1 | 0.01% |
|  | xid_48 | 2 | 0.02% |
|  | xid_61 | 13 | 0.10% |
|  | xid_62 | 3 | 0.02% |
|  | xid_69 | 1 | 0.01% |
|  | xid_79 | 37 | 0.29% |
| GPU GSP 错误 | xid_119 | 1 | 0.01% |
| 总计 |  | 12970 | 100.00% |

| 英文 | 中文 |
|------|------|
| Table VII: Raw Data of Memory and Network Failures from 2023 to 2024, as Mentioned in section VII-C2, Figure 10: “Main Memory" indicates CPU Memory ECC errors, "Network" indicates Network Flash Cuts, and $\mathrm { \^ { 6 6 } x i d s ^ { \prime } }$ are related to GPU memory ECC errors. | 表 VII：2023 至 2024 年内存与网络故障的原始数据，见第七节-C2、图 10："主内存（Main Memory）"表示 CPU 内存 ECC 错误，"网络（Network）"表示网络闪断，"xids"与 GPU 内存 ECC 错误相关。 |

**英文表**

|  | Main Memory | Network | xid_63 | xid_64 | xid_79 | xid_94 | xid_95 | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 |
| October | 4 | 29 | 21 | 0 | 0 | 0 | 0 | 54 |
| November | 14 | 8 | 22 | 0 | 0 | 4 | 0 | 48 |
| Ddecember | 8 | 17 | 21 | 0 | 4 | 2 | 2 | 54 |
| 2024 |
| January | 11 | 9 | 16 | 1 | 3 | 1 | 1 | 42 |
| February | 8 | 12 | 18 | 0 | 2 | 0 | 3 | 43 |
| March | 9 | 14 | 22 | 0 | 6 | 0 | 0 | 51 |
| Total | 54 | 89 | 120 | 1 | 15 | 7 | 6 | 292 |

**中文表**

| | 主内存 | 网络 | xid_63 | xid_64 | xid_79 | xid_94 | xid_95 | 总计 |
|---|---|---|---|---|---|---|---|---|
| 2023 十月 | 4 | 29 | 21 | 0 | 0 | 0 | 0 | 54 |
| 2023 十一月 | 14 | 8 | 22 | 0 | 0 | 4 | 0 | 48 |
| 2023 十二月 | 8 | 17 | 21 | 0 | 4 | 2 | 2 | 54 |
| 2024 一月 | 11 | 9 | 16 | 1 | 3 | 1 | 1 | 42 |
| 2024 二月 | 8 | 12 | 18 | 0 | 2 | 0 | 3 | 43 |
| 2024 三月 | 9 | 14 | 22 | 0 | 6 | 0 | 0 | 51 |
| 总计 | 54 | 89 | 120 | 1 | 15 | 7 | 6 | 292 |

| 英文 | 中文 |
|------|------|
| Table VIII: Raw Data of IB Network Failures and Flash Cuts Over the Past Year, as Mentioned in Section VII-C2, Figure 11. | 表 VIII：过去一年 IB 网络故障与闪断的原始数据，见第七节-C2、图 11。 |

**英文表**

| Date | Failure Count | Date | Failure Count | Date | Failure Count | Date | Failure Count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2023/4/19 | 1 | 2023/7/8 | 1 | 2023/9/7 | 3 | 2023/12/24 | 5 |
| 2023/4/21 | 1 | 2023/7/10 | 2 | 2023/9/12 | 1 | 2023/12/31 | 1 |
| 2023/4/26 | 1 | 2023/7/12 | 10 | 2023/9/17 | 1 | 2024/1/1 | 1 |
| 2023/4/27 | 4 | 2023/7/13 | 1 | 2023/9/21 | 7 | 2024/1/6 | 1 |
| 2023/4/30 | 1 | 2023/7/18 | 2 | 2023/9/27 | 1 | 2024/1/7 | 1 |
| 2023/5/1 | 1 | 2023/7/20 | 1 | 2023/10/8 | 2 | 2024/1/10 | 2 |
| 2023/5/4 | 2 | 2023/7/23 | 2 | 2023/10/10 | 1 | 2024/1/15 | 1 |
| 2023/5/6 | 2 | 2023/7/24 | 2 | 2023/10/11 | 1 | 2024/1/25 | 1 |
| 2023/5/9 | 2 | 2023/7/26 | 1 | 2023/10/16 | 1 | 2024/1/31 | 2 |
| 2023/5/17 | 2 | 2023/7/29 | 3 | 2023/10/22 | 1 | 2024/2/3 | 5 |
| 2023/5/26 | 1 | 2023/8/6 | 3 | 2023/10/25 | 1 | 2024/2/5 | 1 |
| 2023/5/27 | 8 | 2023/8/8 | 1 | 2023/10/26 | 3 | 2024/2/17 | 1 |
| 2023/5/28 | 10 | 2023/8/9 | 1 | 2023/10/27 | 2 | 2024/2/22 | 1 |
| 2023/5/30 | 2 | 2023/8/16 | 1 | 2023/10/28 | 1 | 2024/2/23 | 3 |
| 2023/6/5 | 1 | 2023/8/17 | 2 | 2023/11/2 | 1 | 2024/2/26 | 1 |
| 2023/6/6 | 1 | 2023/8/18 | 1 | 2023/11/6 | 1 | 2024/3/1 | 3 |
| 2023/6/8 | 1 | 2023/8/20 | 1 | 2023/11/9 | 1 | 2024/3/5 | 1 |
| 2023/6/14 | 2 | 2023/8/23 | 2 | 2023/11/14 | 1 | 2024/3/11 | 1 |
| 2023/6/16 | 0 | 2023/8/25 | 3 | 2023/11/20 | 1 | 2024/3/16 | 2 |
| 2023/6/17 | 2 | 2023/8/26 | 4 | 2023/11/30 | 3 | 2024/3/18 | 1 |
| 2023/6/20 | 3 | 2023/8/28 | 4 | 2023/12/7 | 5 | 2024/3/24 | 1 |
| 2023/6/26 | 1 | 2023/8/31 | 7 | 2023/12/9 | 1 | 2024/3/25 | 1 |
| 2023/6/27 | 2 | 2023/9/1 | 3 | 2023/12/10 | 1 | 2024/3/29 | 2 |
| 2023/7/4 | 2 | 2023/9/4 | 1 | 2023/12/14 | 1 | 2024/3/30 | 1 |
| 2023/7/6 | 2 | 2023/9/5 | 3 | 2023/12/22 | 3 | 2024/3/31 | 1 |
| 2023/7/7 | 10 |  |  |  |  |  |  |

**中文表**

| 日期 | 故障数 | 日期 | 故障数 | 日期 | 故障数 | 日期 | 故障数 |
|---|---|---|---|---|---|---|---|
| 2023/4/19 | 1 | 2023/7/8 | 1 | 2023/9/7 | 3 | 2023/12/24 | 5 |
| 2023/4/21 | 1 | 2023/7/10 | 2 | 2023/9/12 | 1 | 2023/12/31 | 1 |
| 2023/4/26 | 1 | 2023/7/12 | 10 | 2023/9/17 | 1 | 2024/1/1 | 1 |
| 2023/4/27 | 4 | 2023/7/13 | 1 | 2023/9/21 | 7 | 2024/1/6 | 1 |
| 2023/4/30 | 1 | 2023/7/18 | 2 | 2023/9/27 | 1 | 2024/1/7 | 1 |
| 2023/5/1 | 1 | 2023/7/20 | 1 | 2023/10/8 | 2 | 2024/1/10 | 2 |
| 2023/5/4 | 2 | 2023/7/23 | 2 | 2023/10/10 | 1 | 2024/1/15 | 1 |
| 2023/5/6 | 2 | 2023/7/24 | 2 | 2023/10/11 | 1 | 2024/1/25 | 1 |
| 2023/5/9 | 2 | 2023/7/26 | 1 | 2023/10/16 | 1 | 2024/1/31 | 2 |
| 2023/5/17 | 2 | 2023/7/29 | 3 | 2023/10/22 | 1 | 2024/2/3 | 5 |
| 2023/5/26 | 1 | 2023/8/6 | 3 | 2023/10/25 | 1 | 2024/2/5 | 1 |
| 2023/5/27 | 8 | 2023/8/8 | 1 | 2023/10/26 | 3 | 2024/2/17 | 1 |
| 2023/5/28 | 10 | 2023/8/9 | 1 | 2023/10/27 | 2 | 2024/2/22 | 1 |
| 2023/5/30 | 2 | 2023/8/16 | 1 | 2023/10/28 | 1 | 2024/2/23 | 3 |
| 2023/6/5 | 1 | 2023/8/17 | 2 | 2023/11/2 | 1 | 2024/2/26 | 1 |
| 2023/6/6 | 1 | 2023/8/18 | 1 | 2023/11/6 | 1 | 2024/3/1 | 3 |
| 2023/6/8 | 1 | 2023/8/20 | 1 | 2023/11/9 | 1 | 2024/3/5 | 1 |
| 2023/6/14 | 2 | 2023/8/23 | 2 | 2023/11/14 | 1 | 2024/3/11 | 1 |
| 2023/6/16 | 0 | 2023/8/25 | 3 | 2023/11/20 | 1 | 2024/3/16 | 2 |
| 2023/6/17 | 2 | 2023/8/26 | 4 | 2023/11/30 | 3 | 2024/3/18 | 1 |
| 2023/6/20 | 3 | 2023/8/28 | 4 | 2023/12/7 | 5 | 2024/3/24 | 1 |
| 2023/6/26 | 1 | 2023/8/31 | 7 | 2023/12/9 | 1 | 2024/3/25 | 1 |
| 2023/6/27 | 2 | 2023/9/1 | 3 | 2023/12/10 | 1 | 2024/3/29 | 2 |
| 2023/7/4 | 2 | 2023/9/4 | 1 | 2023/12/14 | 1 | 2024/3/30 | 1 |
| 2023/7/6 | 2 | 2023/9/5 | 3 | 2023/12/22 | 3 | 2024/3/31 | 1 |
| 2023/7/7 | 10 |  |  |  |  |  |  |
