import React, { useEffect, useState } from 'react';
import { ArticlesContextType, IArticle } from '@types';

type Props = {
    children: React.ReactNode;
};

const ArticlesContext = React.createContext<ArticlesContextType | null>(null);

const ArticlesContextProvider: React.FC<Props> = ({ children }) => {
    const [articles, setArticles] = useState<IArticle[]>([]);
    const [page, setPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const [fullText, setFullText] = useState<string>('');
    const [daysSincePublication, setDaysSincePublication] = useState<number>(7);
    const pageSize = 20;

    const incrementPage = () => {
        if (page < totalPages) {
            setPage(page + 1);
        }
    };

    const decrementPage = () => {
        if (page > 1) {
            setPage(page - 1);
        }
    };

    const resetPage = () => {
        setPage(1);
    };

    const updateTotalPages = (articles: Array<IArticle>) => {
        if (!articles.length) {
            setTotalPages(1);
        }

        setTotalPages(Math.ceil(articles[0].meta.count.total / pageSize));
    };

    const updateFullText = (query: string) => {
        setFullText(query);
        resetPage();
    };

    const updateDaysSincePublication = (days: number) => {
        setDaysSincePublication(days);
        resetPage();
    };

    useEffect(() => {
        const fetchArticles = () => {
            fetch('https://api.geneassocwatch.com/articles', {
                method: 'POST',
                body: JSON.stringify({
                    page: page,
                    pageSize,
                    ...(fullText && { fullText }),
                    daysSincePublication,
                }),
                headers: {
                    'Content-Type': 'application/json',
                },
            })
                .then((res) => res.json())
                .then((articles) => {
                    setArticles(articles);
                    updateTotalPages(articles);
                })
                .catch((err) => console.log('An error occured.'));
        };

        fetchArticles();
    }, [page, fullText, daysSincePublication]);

    return (
        <ArticlesContext.Provider
            value={{
                articles,
                page,
                totalPages,
                incrementPage,
                decrementPage,
                updateFullText,
                updateDaysSincePublication,
            }}
        >
            {children}
        </ArticlesContext.Provider>
    );
};

export { ArticlesContext, ArticlesContextProvider };
