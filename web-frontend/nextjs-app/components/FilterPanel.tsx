import clsx from 'clsx';
import { useState, useRef } from 'react';
import TextInput from '@/components/TextInput';
import PubDateSlider from '@/components/PubDateSlider';
import useArticlesContext from '@/hooks/useArticlesContext';

interface Props {
    className?: string;
}

const FilterPanel = ({ className }: Props) => {
    const { updateFullText, updateDaysSincePublication } =
        useArticlesContext()!;

    const [query, setQuery] = useState<string>('');
    const [days, setDays] = useState<number>(7);

    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        updateFullText(query);
        updateDaysSincePublication(days);
    };

    const formRef = useRef<HTMLFormElement>(null);

    return (
        <form
            ref={formRef}
            onSubmit={(event: React.FormEvent<HTMLFormElement>) =>
                handleSubmit(event)
            }
            className={clsx('grid gap-2.5 bg-white p-4 rounded-lg', className)}
        >
            <TextInput
                handleChange={(newValue: string) => setQuery(newValue)}
                placeholder="Search by keyword"
                className="w-full"
            />

            <PubDateSlider
                value={days}
                handleChange={(value: number | number[]) => {
                    setDays(value as number);
                    formRef?.current?.dispatchEvent(
                        new Event('submit', { cancelable: true, bubbles: true })
                    );
                }}
                className="mr-3"
            />
        </form>
    );
};

export default FilterPanel;
