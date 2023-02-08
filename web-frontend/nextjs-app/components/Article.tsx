import clsx from 'clsx';
import dayjs from 'dayjs';
import { IArticle } from '@types';
import Link from '@/components/Link';

interface Props {
    article: IArticle;
}

const Article = ({ article }: Props) => {
    const associations = article.gda.map((association, index) => (
        <li key={index} className="text-sm leading-snug text-slate-900">
            {association.sentence}
        </li>
    ));

    const authors = article.authors.map((author, index) => (
        <li
            key={index}
            className="flex items-center gap-1.5 text-xs font-medium text-slate-500"
            style={{ lineHeight: '1.2em' }}
        >
            {author.fullName}
            <div
                className={clsx('w-1 h-1 bg-slate-500 rounded-full', {
                    hidden: index === article.authors.length - 1,
                })}
            ></div>
        </li>
    ));

    return (
        <div className="grid gap-2 bg-white rounded-lg p-4">
            <div className="flex justify-between text-sm text-sky-600 font-medium">
                <div>
                    <Link
                        href={`https://pubmed.ncbi.nlm.nih.gov/${article.pmid}`}
                    >
                        PMID{article.pmid}
                    </Link>
                </div>
                <div>
                    {dayjs(article.firstPublicationDate.$date).format(
                        'D MMM YYYY'
                    )}
                </div>
            </div>
            <h3 className="text-base font-medium text-cyan-600">
                <Link href={`https://pubmed.ncbi.nlm.nih.gov/${article.pmid}`}>
                    {article.title}
                </Link>
            </h3>
            <div className="grid gap-1">
                <ul className="flex flex-wrap gap-1.5">{authors}</ul>
                <p className="text-xs font-medium text-cyan-600">
                    {article.journal}
                </p>
            </div>
            <ul className="grid gap-2 list-disc list-inside">{associations}</ul>
        </div>
    );
};

export default Article;
