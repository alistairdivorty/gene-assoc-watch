export interface IArticle {
    _id: { $oid: string };
    pmid: string;
    journal: string;
    firstPublicationDate: { $date: string };
    authors: Array<{
        fullName: string;
        firstName: string;
        lastName: string;
        initials: string;
    }>;
    title: string;
    abstract: string;
    gda: Array<{
        sentence: string;
        score: number;
    }>
    meta: {
        count: {
            total: number;
        }
    }
}

export type ArticlesContextType = {
    articles: IArticle[];
    page: number;
    totalPages: number;
    incrementPage: () => void;
    decrementPage: () => void;
    updateFullText: (query: string) => void;
    updateDaysSincePublication: (days: number) => void;
};
