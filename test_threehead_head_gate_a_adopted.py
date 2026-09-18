from threehead_head_gate_a_adopted import (
    passes_adopted_head_gate,
    ADOPTED_HEAD_GATE_NAME,
)

def base():
    return {
        "race_no": 12,
        "pre_score": 0.925,
        "post_motor_rank_edge2": 0.20,
        "post_ex_rank3": 1.0,
    }

def main():
    assert ADOPTED_HEAD_GATE_NAME == "3HEAD_A_PRECISION_V1"

    # Exact frozen boundaries pass.
    assert passes_adopted_head_gate(base()) is True

    # Each frozen threshold fails immediately on the wrong side.
    x=base(); x["race_no"]=13
    assert passes_adopted_head_gate(x) is False

    x=base(); x["pre_score"]=0.924999
    assert passes_adopted_head_gate(x) is False

    x=base(); x["post_motor_rank_edge2"]=0.199999
    assert passes_adopted_head_gate(x) is False

    x=base(); x["post_ex_rank3"]=2
    assert passes_adopted_head_gate(x) is False

    # Missing/non-finite required inputs fail closed.
    for k in list(base()):
        x=base(); x.pop(k)
        assert passes_adopted_head_gate(x) is False

    x=base(); x["pre_score"]=float("nan")
    assert passes_adopted_head_gate(x) is False

    print("3HEAD_A_PRECISION_V1_FREEZE_OK")

if __name__ == "__main__":
    main()
