import clsx from 'clsx';

interface Props {
    className?: string;
}

const BrandName = ({ className }: Props) => (
    <span
        className={clsx(
            'font-oxanium font-medium whitespace-nowrap tracking-wide',
            className
        )}
    >
        <span className="text-cyan-700">Gene</span>
        <span className="text-pink-500">Assoc</span>
        <span className="text-sky-600">Watch</span>
    </span>
);

export default BrandName;
