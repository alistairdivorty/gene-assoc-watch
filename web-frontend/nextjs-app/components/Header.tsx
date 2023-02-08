import React from 'react';
import clsx from 'clsx';
import BrandName from '@/components/BrandName';

interface Props {
    scrolled: boolean;
}

const Header = ({ scrolled }: Props) => {
    return (
        <header
            className={clsx(
                'fixed top-0 w-screen p-5 text-white z-10 transition-colors duration-300 backdrop-blur-sm',
                {
                    'bg-transparent': !scrolled,
                    'bg-slate-300/80': scrolled,
                }
            )}
        >
            <BrandName className="text-2xl lg:text-3xl" />
        </header>
    );
};

export default Header;
