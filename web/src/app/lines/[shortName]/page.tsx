import { LineDetail } from "./line-detail";

// On-demand dynamic route (no generateStaticParams). @cloudflare/next-on-pages
// runs SSR routes on the Edge runtime.
export const runtime = "edge";

interface Props {
  params: Promise<{ shortName: string }>;
}

const Page = async ({ params }: Props) => {
  const { shortName } = await params;
  const decoded = decodeURIComponent(shortName);
  return <LineDetail shortName={decoded} />;
};

export default Page;
