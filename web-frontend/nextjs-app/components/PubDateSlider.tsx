import Slider from '@mui/material/Slider';
import clsx from 'clsx';

interface Props {
    value: number;
    handleChange: (newValue: number | number[]) => void;
    className?: string;
}

const marks = [
    {
        value: 1,
        label: '1',
    },
    {
        value: 7,
        label: '7',
    },
];

const PubDateSlider = ({ handleChange, className }: Props) => {
    return (
        <div className={clsx(className, 'flex gap-5')}>
            <div className="text-xs text-slate-700 font-medium">
                Days since
                <br />
                publication:
            </div>
            <Slider
                size="small"
                sx={{
                    color: '#0891b2',
                    '& .MuiSlider-markLabel': {
                        top: 18,
                        fontSize: '.8rem',
                        color: '#475569',
                    },
                }}
                min={1}
                max={7}
                defaultValue={7}
                valueLabelDisplay="auto"
                marks={marks}
                valueLabelFormat={(value) => <div>{value + ' days'}</div>}
                onChangeCommitted={(event, value: number | number[]) =>
                    handleChange(value as number)
                }
                className="-translate-y-1"
            />
        </div>
    );
};

export default PubDateSlider;
