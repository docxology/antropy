# Inference and prospective operating characteristics {#sec:power}

## Scientific unit and declared design

Power depends on a specified generating mechanism, estimand, comparison rule and
decision threshold; it is not an intrinsic property of an entropy value. This
simulation evaluates the complete configured procedure using independently
generated whole fields [@morris2019simulation]. Pixels and overlapping template
pairs contribute to an estimator but do not become independent experimental
subjects. A same-probability stochastic scenario provides the null control;
alternative scenarios change the generating replacement probability.

{{POWER_NARRATIVE}}

Sample-size comparisons reuse prefixes of each maximum-size subject pool.
Within a given cell, outer repetitions use separate streams; estimates across
sample sizes and estimators need not be independent. Reported
intervals are pointwise rather than simultaneous confidence bands. The
configured target is a planning input, not a certified sample-size recommendation
or an estimate of post hoc observed power.

## Permutation decisions and multiplicity

For independent field groups, the statistic is the second-group mean minus the
first-group mean. The null assumption is exchangeability of the whole-field
observations under identical generating distributions. The separate paired API
uses within-pair contrasts and exchangeable sign flips; the current field
generator supplies independent groups instead.

With exact enumeration, $p=e/A$ for $e$ inclusive-tail allocations among all $A$
allocations, including the observed allocation. With $B$ sampled allocations,
the Monte Carlo correction is $p=(b+1)/(B+1)$ [@phipson2010permutation]. Inclusive
tails are compared using exact rational contrasts of the stored binary64 inputs;
reporting a floating-point effect does not change the tail decision. The recorded
p-value grid increment need not equal the smallest attainable two-sided p-value,
because complementary allocations can have the same absolute statistic.

When Holm adjustment is selected, ordered p-values use the running maximum
of $(K-i+1)p_{(i)}$, clipped at one and returned to the original order
[@holm1979]. The declared family includes every configured estimator. Unavailable
comparisons keep null observed p-values and cannot reject; a value of one is used
only internally for conservative family bookkeeping. Raw and adjusted rejection
counts remain separate in the producer report.

## Availability, rejection rates and uncertainty

Let $R$ be attempted outer repetitions, $C$ available comparisons, $U=R-C$
unavailable comparisons and $J$ selected rejections. The report distinguishes

$$
\widehat q_{\mathrm{conditional}}=J/C\quad(C>0),\qquad
\widehat q_{\mathrm{procedure}}=J/R,\qquad
\widehat a=C/R.
$$ {#eq:power-denominators}

Conditional rejection is undefined when no comparison is available. The
unconditional rate describes the implemented procedure that declines to reject
on unavailable comparisons. Under a null scenario it is a false-positive
operating characteristic; under a declared alternative it is a prospective
detection rate. Neither quantity is a biological classification accuracy.

Wilson score intervals quantify binomial Monte Carlo uncertainty at the
configured confidence level [@brown2001interval]. If $\widehat q=J/R$ and $z$ is
the configured normal quantile, their center and half-width are

$$
c=\frac{\widehat q+z^2/(2R)}{1+z^2/R},\qquad
h=\frac{z\sqrt{\widehat q(1-\widehat q)/R+z^2/(4R^2)}}{1+z^2/R}.
$$ {#eq:wilson}

The separate interval conditional on availability uses denominator $C$.
Missing-decision identification bounds $[J/R,(J+U)/R]$ are sensitivity bounds,
not confidence intervals. They show the range obtained by leaving unknown
decisions unresolved rather than imputing zero entropy or deleting a field.

For a true cell rejection probability $q$, the outer simulation standard error
is $\sqrt{q(1-q)/R}$, bounded above by $1/(2\sqrt R)$. This bound concerns
simulation precision. It does not quantify an entropy estimator's bias or
guarantee the configured power target is attained.

{{POWER_REJECTION_TABLE}}

{{POWER_REJECTION_FIGURE}}

{{POWER_AVAILABILITY_TABLE}}

{{POWER_AVAILABILITY_FIGURE}}

## Effect summaries and bootstrap interface

Mean differences retain each estimator's configured units. Their reported means
and sample standard deviations condition on available comparisons; unavailable
effects remain null. Empirical variation among outer repetitions and the
Monte Carlo uncertainty of a rejection proportion are different quantities.

{{POWER_EFFECT_TABLE}}

The public percentile-bootstrap interface resamples whole observations within
independent groups, or paired observations jointly, and returns configured
empirical-quantile bounds [@efron1979bootstrap]. It is a separate inference tool;
the operating-characteristic simulation uses permutation decisions and Wilson
intervals. For bootstrap contrasts $D^*=\overline Y^*-\overline X^*$ and configured
confidence level $c$, the percentile limits are
$[Q_{(1-c)/2}(D^*),Q_{(1+c)/2}(D^*)]$, using linear interpolation of empirical
quantiles. The paired variant resamples subject pairs together and retains their
within-pair dependence. Small, discrete, sparse and degenerate samples can limit percentile
coverage. Application-specific dependence, effect size, generating assumptions
and external validation remain necessary before choosing a scientific sample
size or transferring the synthetic results to ant behavior.
