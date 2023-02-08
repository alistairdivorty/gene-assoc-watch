import clsx from 'clsx';
import Head from 'next/head';
import Hero from '@/components/Hero';
import PaginationMenu from '@/components/PaginationMenu';
import FilterPanel from '@/components/FilterPanel';
import Articles from '@/components/Articles';
import useArticlesContext from '@/hooks/useArticlesContext';

export default function Home() {
    const { articles } = useArticlesContext() ?? {};

    return (
        <>
            <Head>
                <title>GeneAssocWatch</title>
                <meta
                    name="description"
                    content="An AI powered tool for monitoring newly published information on gene–disease associations."
                />
                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1"
                />
                <link rel="icon" href="/favicon.ico" />
            </Head>
            <main className="grid pb-10 bg-slate-200">
                <Hero />
                <div className="w-full min-h-screen flex justify-center pt-4">
                    <div className="m-4 w-full max-w-3xl">
                        <div className="w-full flex justify-center mt-4 mb-8">
                            <FilterPanel className="w-full" />
                        </div>
                        <div className="w-full flex justify-center my-4">
                            <PaginationMenu />
                        </div>
                        <Articles articles={articles ?? []} />
                        <div
                            className={clsx('w-full flex justify-center my-4', {
                                hidden: !(articles ?? []).length,
                            })}
                        >
                            <PaginationMenu />
                        </div>
                    </div>
                </div>
            </main>
        </>
    );
}
