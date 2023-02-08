import Layout from '@/components/Layout';
import '../styles/globals.css';
import type { AppProps } from 'next/app';
import { Oxanium, Montserrat } from '@next/font/google';
import { ArticlesContextProvider } from '@/context/articlesContext';

const oxanium = Oxanium({
    subsets: ['latin'],
    variable: '--font-oxanium',
});

const montserrat = Montserrat({
    subsets: ['latin'],
    variable: '--font-montserrat',
});

export default function App({ Component, pageProps }: AppProps) {
    return (
        <main
            className={`${montserrat.variable} ${oxanium.variable} font-montserrat`}
        >
            <ArticlesContextProvider>
                <Layout>
                    <Component {...pageProps} />
                </Layout>
            </ArticlesContextProvider>
        </main>
    );
}
