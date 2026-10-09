# Copyright (c) 2026 Daniel Ari Friedman
"""Independent ordinal-pattern examples, spatial geometry and rejection controls."""

import math
from collections import Counter
from itertools import product

import numpy as np
import pytest
from pydantic import ValidationError

from antropy_hd.errors import ParameterError, ResourceError
from antropy_hd.models import EmbeddingConfig, Status
from antropy_hd.ordinal import permutation_entropy, weighted_permutation_entropy


def test_permutation_when_binary_patterns_have_known_counts() -> None:
    # Given two increasing pairs and one decreasing pair.
    data = [0, 2, 1, 3]
    expected = -(2 / 3) * math.log2(2 / 3) - (1 / 3) * math.log2(1 / 3)
    # When local pair entropy is computed.
    result = permutation_entropy(data)
    # Then it equals the independently known motif entropy.
    assert result.value == pytest.approx(expected)


def test_weighted_permutation_when_variances_differ_uses_population_weights() -> None:
    # Given increasing-pair variance mass 2 and decreasing-pair mass 1/4.
    data = [0, 2, 1, 3]
    expected = -(8 / 9) * math.log2(8 / 9) - (1 / 9) * math.log2(1 / 9)
    # When variance-weighted pattern entropy is computed.
    result = weighted_permutation_entropy(data)
    # Then amplitude information changes the independently known probabilities.
    assert result.value == pytest.approx(expected)


def test_permutation_when_local_values_tie_uses_positional_order() -> None:
    # Given an equal-value pair followed by a descending pair.
    data = [1, 1, 0]
    # When deterministic positional ties are used.
    result = permutation_entropy(data)
    # Then two distinct motifs have equal probability.
    assert result.value == pytest.approx(1)


def test_permutation_when_input_is_two_dimensional_retains_windows() -> None:
    # Given four distinct 2x2 ordinal motifs.
    data = np.array([[1, 4, 2], [3, 0, 5], [6, 7, 8]])
    # When spatial permutation entropy is computed.
    result = permutation_entropy(data)
    # Then the four spatial windows form a uniform four-symbol distribution.
    assert result.n_observations == 4
    assert result.value == pytest.approx(2)
    assert result.diagnostics["pattern_length"] == 4


def test_permutation_when_normalized_uses_possible_patterns() -> None:
    # Given four observed motifs among 4! possible local orderings.
    data = np.array([[1, 4, 2], [3, 0, 5], [6, 7, 8]])
    # When normalization is requested.
    result = permutation_entropy(data, normalize=True)
    # Then the denominator is log2(4!), rather than the observed motif count.
    assert result.value == pytest.approx(2 / math.log2(24))


def test_permutation_when_input_is_three_dimensional_matches_python_oracle() -> None:
    # Given a rectangular spatial embedding and an independent Python motif count.
    data = np.random.default_rng(821).normal(size=(2, 3, 3))
    patterns: Counter[tuple[int, ...]] = Counter()
    for plane, row, column in product(range(2), range(2), range(2)):
        values = [
            float(data[plane, row + dy, column + dx]) for dy, dx in product(range(2), range(2))
        ]
        patterns[tuple(sorted(range(4), key=values.__getitem__))] += 1
    expected = -sum((count / 8) * math.log2(count / 8) for count in patterns.values())
    # When native-dimensional templates are used.
    result = permutation_entropy(data, embedding=EmbeddingConfig(shape=(1, 2, 2)))
    # Then their entropy agrees with the separately enumerated spatial oracle.
    assert result.value == pytest.approx(expected)
    assert result.n_observations == 8


def test_permutation_when_delay_and_stride_are_set_uses_declared_origins() -> None:
    # Given pairs (0,3), (3,2), (2,4), separated by ignored intervening values.
    data = [0, 10, 3, 20, 2, 30, 4]
    expected = -(2 / 3) * math.log2(2 / 3) - (1 / 3) * math.log2(1 / 3)
    # When delay two and origin stride two are requested.
    result = permutation_entropy(data, embedding=EmbeddingConfig(delay=2, stride=2))
    # Then only the three declared pairs contribute.
    assert result.value == pytest.approx(expected)
    assert result.n_observations == 3


def test_permutation_when_values_are_monotonically_transformed_is_invariant() -> None:
    # Given a strictly monotone transformation preserving every ordinal pattern.
    data = np.random.default_rng(32).uniform(0.1, 2.0, size=(4, 4))
    expected = permutation_entropy(data).value
    # When the transformed spatial field is analyzed.
    result = permutation_entropy(np.exp(data))
    # Then its ordinal entropy is unchanged.
    assert result.value == pytest.approx(expected)


def test_weighted_permutation_when_amplitudes_are_huge_is_scale_invariant() -> None:
    # Given pair variances whose direct squares would overflow float64.
    data = np.array([0.0, 2.0, 1.0, 3.0])
    expected = -(8 / 9) * math.log2(8 / 9) - (1 / 9) * math.log2(1 / 9)
    # When a huge common amplitude factor is applied.
    result = weighted_permutation_entropy(data * 1e307)
    # Then normalized variance weights preserve the correct finite entropy.
    assert result.value == pytest.approx(expected)


def test_weighted_permutation_when_offset_is_huge_preserves_small_variance_weights() -> None:
    # Given exactly represented fluctuations over a huge common baseline.
    x = np.array([0, 1, 2, 0, 1, 0, 2, 1]) * np.spacing(1e308) + 1e308
    y = x - x[0]
    config = EmbeddingConfig(shape=3)
    expected = weighted_permutation_entropy(y, embedding=config).value
    # When variance weights are computed in the original high-offset field.
    result = weighted_permutation_entropy(x, embedding=config)
    # Then translation preserves the representable fluctuations and their weights.
    assert result.value == pytest.approx(expected, abs=1e-14)


def test_weighted_permutation_when_windows_have_distinct_large_offsets_preserves_weights() -> None:
    # Given disjoint spatial rows with different large baselines and local fluctuations.
    steps = np.array([[0, 1, 2, 0, 1], [2, 0, 1, 0, 2]]) * np.spacing(1e308)
    x = steps + np.array([[1e308], [-1e308]])
    y = x - x[:, :1]
    config = EmbeddingConfig(shape=(1, 3))
    expected = weighted_permutation_entropy(y, embedding=config).value
    # When variance is evaluated within each spatial window.
    result = weighted_permutation_entropy(x, embedding=config)
    # Then each window's additive baseline leaves its own variance weight unchanged.
    assert result.value == pytest.approx(expected, abs=1e-14)


def test_permutation_when_input_is_constant_has_one_pattern() -> None:
    # Given a constant spatial field.
    data = np.ones((3, 3))
    # When stable ties are resolved.
    result = permutation_entropy(data)
    # Then all local windows map to one ordering.
    assert result.value == 0


def test_weighted_permutation_when_all_windows_have_zero_variance_is_undefined() -> None:
    # Given constant windows with zero total variance weight.
    data = np.ones((3, 3))
    # When weighted entropy is requested.
    result = weighted_permutation_entropy(data)
    # Then no frequency distribution is silently substituted.
    assert result.status is Status.UNDEFINED
    assert result.value is None


def test_weighted_permutation_when_all_values_are_zero_is_undefined() -> None:
    # Given zero-valued windows and a zero global scaling factor.
    data = np.zeros((3, 3))
    # When local variance weights are computed.
    result = weighted_permutation_entropy(data)
    # Then the zero-mass distribution remains explicitly undefined.
    assert result.status is Status.UNDEFINED


def test_permutation_when_normalized_pattern_is_singleton_is_undefined() -> None:
    # Given local windows of one sample and only 1! possible motifs.
    data = [1, 2, 3]
    # When zero-maximum normalization is requested.
    result = permutation_entropy(data, embedding=EmbeddingConfig(shape=1), normalize=True)
    # Then division by log(1!) is represented explicitly.
    assert result.status is Status.UNDEFINED


def test_permutation_when_pattern_limit_is_exceeded_rejects_it() -> None:
    # Given a 4x4 block containing sixteen ordinal positions.
    data = np.arange(25).reshape(5, 5)
    # When the default ten-position alphabet limit is used.
    # Then the large pattern computation is rejected.
    with pytest.raises(ResourceError, match="max_pattern_length"):
        permutation_entropy(data, embedding=EmbeddingConfig(shape=4))


def test_permutation_when_working_storage_exceeds_budget_rejects_it() -> None:
    # Given templates that fit a 1024-byte base-storage limit but whose ranks do not.
    data = np.arange(15)
    # When the explicit working-memory budget is applied.
    # Then the rank/sort allocations are guarded.
    with pytest.raises(ResourceError, match="max_memory_bytes"):
        permutation_entropy(data, embedding=EmbeddingConfig(max_memory_bytes=1024))


def test_permutation_when_template_limit_is_exceeded_rejects_it() -> None:
    # Given nine valid pair origins and a two-template limit.
    data = np.arange(10)
    # When template materialization is requested.
    # Then the shared geometry guard rejects the request.
    with pytest.raises(ResourceError, match="max_templates"):
        permutation_entropy(data, embedding=EmbeddingConfig(max_templates=2))


def test_permutation_when_embedding_span_is_invalid_rejects_it() -> None:
    # Given an embedding wider than the input axis.
    # When ordinal entropy is requested.
    # Then no truncated window is substituted.
    with pytest.raises(ParameterError, match="shape"):
        permutation_entropy([1, 2], embedding=EmbeddingConfig(shape=3))


@pytest.mark.parametrize("length", [0, 1, 33, True])
def test_permutation_when_pattern_limit_is_invalid_rejects_it(length: int) -> None:
    # Given an invalid algorithm resource configuration.
    # When it enters the ordinal-options boundary.
    # Then the configuration fails validation.
    with pytest.raises(ValidationError):
        permutation_entropy([1, 2, 3], max_pattern_length=length)
