import { IArticle } from '@types';
import Article from '@/components/Article';

interface Props {
    articles: IArticle[];
}

const Articles = ({ articles }: Props) => {
    const articleElements = articles.map((article) => (
        <li key={article._id.$oid}>
            <div className="relative">
                <Article article={article} />
            </div>
        </li>
    ));

    return <ul className="grid gap-4 lg:gap-8">{articleElements}</ul>;
};

export default Articles;
