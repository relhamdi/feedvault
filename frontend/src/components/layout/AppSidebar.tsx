import { Badge } from "@/components/ui/badge";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { useSources } from "@/hooks/useSources";
import type { Source } from "@/types";

interface AppSidebarProps {
  selectedSourceId: number | null;
  onSelectSource: (id: number) => void;
}

function SourceItem({
  source,
  isSelected,
  onSelect,
}: {
  source: Source;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        isActive={isSelected}
        onClick={onSelect}
        className="flex items-center gap-3 py-2"
      >
        {/* source icon or colored placeholder */}
        <div
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-bold text-white"
          style={{ backgroundColor: source.color ?? "#6366f1" }}
        >
          {source.name.charAt(0).toUpperCase()}
        </div>

        {/* active indicator */}
        <span
          className={`h-2 w-2 shrink-0 rounded-full ${source.is_active ? "bg-green-500" : "bg-muted-foreground"}`}
        />

        <span className="flex-1 truncate text-sm">{source.name}</span>

        {/* unread badge — placeholder 0 until we have unread count from API */}
        <Badge variant="secondary" className="ml-auto shrink-0">
          0
        </Badge>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
}

export function AppSidebar({
  selectedSourceId,
  onSelectSource,
}: AppSidebarProps) {
  const { data: sources, isLoading } = useSources();

  return (
    <Sidebar>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Sources</SidebarGroupLabel>
          <SidebarMenu>
            {isLoading && (
              <p className="px-3 text-xs text-muted-foreground">Loading...</p>
            )}
            {sources?.map((source) => (
              <SourceItem
                key={source.id}
                source={source}
                isSelected={selectedSourceId === source.id}
                onSelect={() => onSelectSource(source.id)}
              />
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
