from run_3head_a_live_gate_shadow import exhibition_rank3, parse_exhibition_times

def main():
    assert exhibition_rank3([6.80,6.79,6.78,6.81,6.82,6.83]) == 1
    assert exhibition_rank3([6.77,6.79,6.78,6.81,6.82,6.83]) == 2
    # Tie for fastest remains rank 1 because research uses strictly faster count.
    assert exhibition_rank3([6.78,6.80,6.78,6.81,6.82,6.83]) == 1

    body = "data=x\nmeta\n1\t6.80\n2\t6.79\n3\t6.78\n4\t6.81\n5\t6.82\n6\t6.83\n"
    assert parse_exhibition_times(body) == [6.80,6.79,6.78,6.81,6.82,6.83]
    print("3HEAD_A_SHADOW_GATE_SMOKE_OK")

if __name__ == "__main__":
    main()
