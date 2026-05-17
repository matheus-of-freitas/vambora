import { Heading } from "@/shared/components/layout/heading";
import { Stack } from "@/shared/components/layout/stack";
import { Surface } from "@/shared/components/layout/surface";
import { Text } from "@/shared/components/layout/text";
import { ROUTE_COLORS } from "@/shared/components/map/route-colors";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { ScrollArea } from "@/shared/components/ui/scroll-area";
import { Skeleton } from "@/shared/components/ui/skeleton";

const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <Stack gap="md">
    <Heading level={2} variant="section">
      {title}
    </Heading>
    {children}
  </Stack>
);

const DesignPage = () => {
  return (
    <main className="container mx-auto py-10">
      <Stack gap="lg">
        <Stack gap="xs">
          <Heading variant="display">Design system</Heading>
          <Text muted>
            Closed inventory of approved primitives and components. New UI must compose from this
            set or extend it via PR.
          </Text>
        </Stack>

        <Section title="Tokens / brand colors">
          <Stack direction="row" gap="md">
            {(
              [
                { key: "bus", className: "bg-route-bus" },
                { key: "brt", className: "bg-route-brt" },
                { key: "vlt", className: "bg-route-vlt" },
              ] as const
            ).map(({ key, className }) => (
              <Stack key={key} gap="xs" align="center">
                <div
                  className={`h-12 w-12 rounded-md ${className}`}
                  aria-label={`route-${key} swatch`}
                />
                <Text variant="caption" muted>
                  {`route-${key}`}
                </Text>
                <Text variant="caption" muted>
                  {ROUTE_COLORS[key]}
                </Text>
              </Stack>
            ))}
          </Stack>
        </Section>

        <Section title="Headings">
          <Stack gap="sm">
            <Heading variant="display">Display heading</Heading>
            <Heading variant="page">Page heading</Heading>
            <Heading variant="section">Section heading</Heading>
          </Stack>
        </Section>

        <Section title="Text variants">
          <Stack gap="sm">
            <Text variant="body">Body text — the default narrative voice of the app.</Text>
            <Text variant="body" muted>
              Body text, muted — for secondary information.
            </Text>
            <Text variant="caption">Caption — chrome and tight spaces.</Text>
            <Text variant="label">label — uppercase form labels</Text>
          </Stack>
        </Section>

        <Section title="Buttons">
          <Stack direction="row" gap="sm">
            <Button>Default</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="link">Link</Button>
          </Stack>
          <Stack direction="row" gap="sm">
            <Button size="sm">Small</Button>
            <Button>Default size</Button>
            <Button size="lg">Large</Button>
          </Stack>
        </Section>

        <Section title="Badges">
          <Stack direction="row" gap="sm">
            <Badge>Default</Badge>
            <Badge variant="secondary">Secondary</Badge>
            <Badge variant="outline">Outline</Badge>
            <Badge variant="destructive">Destructive</Badge>
          </Stack>
        </Section>

        <Section title="Input">
          <Stack gap="sm" className="max-w-sm">
            <Input placeholder="Buscar linha (ex: 485)" />
            <Input placeholder="Disabled" disabled />
          </Stack>
        </Section>

        <Section title="Card">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Linha 485</CardTitle>
                <CardDescription>BRT TransOeste — Centro ↔ Alvorada</CardDescription>
              </CardHeader>
              <CardContent>
                <Text variant="body">12 vehicles in service · 4 min headway</Text>
              </CardContent>
              <CardFooter>
                <Button size="sm" variant="outline">
                  View details
                </Button>
              </CardFooter>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Sample card</CardTitle>
                <CardDescription>Used for line/stop summaries.</CardDescription>
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-3/4" />
              </CardContent>
            </Card>
          </div>
        </Section>

        <Section title="Surface (overlay)">
          <Surface overlay padding="md">
            <Stack gap="xs">
              <Heading variant="page">Overlay surface</Heading>
              <Text variant="caption" muted>
                The recurring chrome pattern: a translucent card that floats over the map.
              </Text>
            </Stack>
          </Surface>
        </Section>

        <Section title="Skeleton">
          <Stack gap="sm">
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-1/3" />
          </Stack>
        </Section>

        <Section title="ScrollArea">
          <ScrollArea className="h-32 w-full max-w-md rounded-md border p-4">
            <Stack gap="xs">
              {Array.from({ length: 20 }, (_, i) => `Item ${i + 1}`).map((label) => (
                <Text key={label} variant="caption">
                  {label}
                </Text>
              ))}
            </Stack>
          </ScrollArea>
        </Section>

        <Section title="Stack (gaps)">
          <Stack gap="md">
            {(["xs", "sm", "md", "lg"] as const).map((g) => (
              <Stack key={g} direction="row" gap={g} align="center">
                <Badge variant="outline">{`gap=${g}`}</Badge>
                <div className="h-4 w-4 rounded bg-primary" />
                <div className="h-4 w-4 rounded bg-primary" />
                <div className="h-4 w-4 rounded bg-primary" />
              </Stack>
            ))}
          </Stack>
        </Section>
      </Stack>
    </main>
  );
};

export default DesignPage;
