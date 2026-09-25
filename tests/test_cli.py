from aurelia.cli import run_demo


def test_run_demo_output_shape() -> None:
    result = run_demo("How effective is intervention X?")

    assert "question" in result
    assert "safety" in result
    assert "facts" in result
    assert "hypotheses" in result
    assert "uncertainty" in result

    uncertainty = result["uncertainty"]
    assert isinstance(uncertainty, dict)
    assert {"confidence", "coverage", "agreement", "conflict", "limitations", "open_questions"}.issubset(
        uncertainty.keys()
    )
