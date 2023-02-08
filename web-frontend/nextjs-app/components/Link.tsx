import React from 'react';

interface Props {
    children: React.ReactNode;
    href: string;
}

const Link = ({ children, href }: Props) => (
    <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="underline decoration-transparent hover:decoration-inherit transition-colors duration-200"
    >
        {children}
    </a>
);

export default Link;
