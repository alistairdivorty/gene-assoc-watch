import HeroVector from '@/components/HeroVector';
import BrandName from '@/components/BrandName';

const Hero = () => (
    <div className="relative min-h-screen pt-20 bg-slate-100 flex flex-col justify-end w-full overflow-hidden">
        <div className="lg:absolute inset-x-[45%] inset-y-[20%] flex-1 flex items-center justify-center lg:block">
            <div className="max-w-lg grid gap-2 m-5">
                <BrandName className="text-4xl lg:text-6xl" />
                <p className="text-lg font-medium text-slate-700">
                    An AI powered tool for monitoring newly published
                    information on gene–disease associations.
                </p>
            </div>
        </div>
        <HeroVector className="w-full lg:translate-y-32" />
    </div>
);

export default Hero;
