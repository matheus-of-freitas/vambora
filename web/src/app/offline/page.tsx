import { OfflineClient } from "./offline-client";

export const dynamic = "force-static";
export const metadata = {
  title: "Vambora — offline",
};

const Page = () => <OfflineClient />;

export default Page;
