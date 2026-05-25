## Abstract

Nested sampling estimates the evidence by assigning prior volumes to an ordered sequence of likelihood contours.
Markov chain constrained-prior samplers, which are used in high-dimensional problems, generate many intermediate states before producing the next classic sample.
These intermediate states are discarded because their correlation prevents them from being inserted into the ordered NS sequence without changing its order-statistic law.
This paper introduces a novel method of using them to improve evidence estimation, by formulating NS in a Bayesian way and conditioning on phantom samples as Monte Carlo observations.

We then present the open-source software package, JAXNS v3, and its implementation choices.
We validate JAXNS on difficult evidence and posterior-estimation benchmarks for accuracy and performance.
