import { StopDetail } from "./stop-detail";

// On-demand dynamic route (no generateStaticParams). @cloudflare/next-on-pages
// runs SSR routes on the Edge runtime.
export const runtime = "edge";

interface Props {
  params: Promise<{ stopId: string }>;
}

const Page = async ({ params }: Props) => {
  const { stopId } = await params;
  return <StopDetail stopId={decodeURIComponent(stopId)} />;
};

export default Page;
