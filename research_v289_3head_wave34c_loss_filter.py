from pathlib import Path
import shutil
import research_v289_3head_wave34d_group_prototypes as wave34d

if __name__ == '__main__':
    wave34d.main()
    mapping = {
        'analysis_v289_3head_wave34d_group_prototypes.csv': 'analysis_v289_3head_wave34c_loss_filter.csv',
        'research_v289_3head_wave34d_group_prototypes.json': 'research_v289_3head_wave34c_loss_filter.json',
        'research_v289_3head_wave34d_group_prototypes.md': 'research_v289_3head_wave34c_loss_filter.md',
    }
    for src, dst in mapping.items():
        if not Path(src).exists():
            raise RuntimeError(f'missing Wave34d output: {src}')
        shutil.copyfile(src, dst)
