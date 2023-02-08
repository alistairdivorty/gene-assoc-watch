import clsx from 'clsx';

interface Props {
    handleChange: (value: string) => void;
    placeholder?: string;
    className?: string;
}

const TextInput = ({ handleChange, placeholder, className }: Props) => {
    return (
        <div className="relative">
            <input
                type="text"
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                    handleChange(event.target.value)
                }
                placeholder={placeholder}
                className={clsx(
                    'bg-white rounded py-1.5 pl-2 pr-10 border border-slate-300 outline-none ring-1 ring-transparent focus:ring-sky-400 focus:border-transparent transition-all duration-200 text-slate-800 placeholder:text-slate-500 text-sm',
                    className
                )}
            />
            <button type="submit">
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="absolute right-2 top-1/2 -translate-y-1/2 w-5 h-5 hover:text-sky-400 transition-colors duration-200"
                >
                    <path
                        fillRule="evenodd"
                        d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
                        clipRule="evenodd"
                    />
                </svg>
            </button>
        </div>
    );
};

export default TextInput;
