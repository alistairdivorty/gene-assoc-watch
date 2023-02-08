import useArticlesContext from '@/hooks/useArticlesContext';
import clsx from 'clsx';

const PaginationMenu = () => {
    const { page, totalPages, incrementPage, decrementPage } =
        useArticlesContext() ?? {};

    const handlePaginate = (direction: 'forward' | 'backward') => {
        if (incrementPage && decrementPage) {
            direction === 'forward' ? incrementPage() : decrementPage();
        }
    };

    const chevronLeft = (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="w-5 h-5"
        >
            <path
                fillRule="evenodd"
                d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z"
                clipRule="evenodd"
            />
        </svg>
    );

    const chevronRight = (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="w-5 h-5"
        >
            <path
                fillRule="evenodd"
                d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                clipRule="evenodd"
            />
        </svg>
    );

    return (
        <nav className="flex items-center gap-2 text-slate-700 text-sm font-medium">
            <button
                onClick={() => handlePaginate('backward')}
                disabled={page === 1}
            >
                {chevronLeft}
            </button>
            Page {page} of {totalPages}
            <button
                onClick={() => handlePaginate('forward')}
                disabled={page === totalPages}
            >
                {chevronRight}
            </button>
        </nav>
    );
};

export default PaginationMenu;
