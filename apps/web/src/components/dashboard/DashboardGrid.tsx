"use client";

import * as React from "react";
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { motion } from "framer-motion";

import { cn } from "@/lib/utils";
import { TrustTimeline } from "@/components/dashboard/widgets/TrustTimeline";
import { SemanticDriftMatrix } from "@/components/dashboard/widgets/SemanticDriftMatrix";
import { ThreatTicker } from "@/components/dashboard/widgets/ThreatTicker";
import { RuntimePosture } from "@/components/dashboard/widgets/RuntimePosture";
import { SelfHealingActions } from "@/components/dashboard/widgets/SelfHealingActions";

type WidgetId =
  | "trust"
  | "drift"
  | "runtime"
  | "threats"
  | "healing";

type WidgetDef = {
  id: WidgetId;
  colSpan: string;
  render: () => React.ReactNode;
};

const WIDGETS: WidgetDef[] = [
  { id: "trust", colSpan: "md:col-span-8", render: () => <TrustTimeline /> },
  { id: "drift", colSpan: "md:col-span-4", render: () => <SemanticDriftMatrix /> },
  { id: "runtime", colSpan: "md:col-span-6", render: () => <RuntimePosture /> },
  { id: "threats", colSpan: "md:col-span-6", render: () => <ThreatTicker /> },
  { id: "healing", colSpan: "md:col-span-12", render: () => <SelfHealingActions /> },
];

const STORAGE_KEY = "daifend.dashboard.widgets.v1";

function useWidgetOrder() {
  const [order, setOrder] = React.useState<WidgetId[]>(() => {
    if (typeof window === "undefined") return WIDGETS.map((w) => w.id);
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return WIDGETS.map((w) => w.id);
      const parsed = JSON.parse(raw) as unknown;
      if (!Array.isArray(parsed)) return WIDGETS.map((w) => w.id);
      const valid = parsed.filter((x): x is WidgetId =>
        WIDGETS.some((w) => w.id === x),
      );
      return valid.length ? valid : WIDGETS.map((w) => w.id);
    } catch {
      return WIDGETS.map((w) => w.id);
    }
  });

  React.useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(order));
    } catch {
      // ignore
    }
  }, [order]);

  return { order, setOrder };
}

function SortableTile({
  id,
  className,
  children,
}: {
  id: WidgetId;
  className?: string;
  children: React.ReactNode;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <motion.div
      ref={setNodeRef}
      style={style}
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: [0.2, 0.9, 0.2, 1] }}
      className={cn(className, isDragging && "opacity-70")}
    >
      {React.isValidElement(children)
        ? React.cloneElement(children, {
            // Most widgets accept `dragHandleProps?: HTMLAttributes<HTMLButtonElement>`.
            // If a widget ignores it, drag still works via keyboard sensor.
            // @ts-expect-error - injected prop for sortable handle
            dragHandleProps: { ...attributes, ...listeners },
          })
        : children}
    </motion.div>
  );
}

export function DashboardGrid() {
  const { order, setOrder } = useWidgetOrder();

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const defsById = React.useMemo(() => {
    const m = new Map<WidgetId, WidgetDef>();
    for (const w of WIDGETS) m.set(w.id, w);
    return m;
  }, []);

  const ordered = order
    .map((id) => defsById.get(id))
    .filter((x): x is WidgetDef => Boolean(x));

  function onDragEnd(e: DragEndEvent) {
    const { active, over } = e;
    if (!over) return;
    if (active.id === over.id) return;
    const oldIndex = order.indexOf(active.id as WidgetId);
    const newIndex = order.indexOf(over.id as WidgetId);
    if (oldIndex < 0 || newIndex < 0) return;
    setOrder(arrayMove(order, oldIndex, newIndex));
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={onDragEnd}
    >
      <SortableContext items={ordered.map((w) => w.id)}>
        <div className="grid gap-4 md:grid-cols-12">
          {ordered.map((w) => (
            <SortableTile key={w.id} id={w.id} className={w.colSpan}>
              {w.render()}
            </SortableTile>
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
}

