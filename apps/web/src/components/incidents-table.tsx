"use client";

import type { IncidentRecord } from "@contracts";
import Link from "next/link";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import { useEffect, useMemo, useState } from "react";

import { acknowledgeIncident, getIncidentsLive } from "@/lib/api";
import { useLiveQuery } from "@/lib/use-live-query";

const severityClass = {
  healthy: "text-emerald-200 bg-emerald-400/12",
  warning: "text-orange-100 bg-orange-300/14",
  critical: "text-rose-100 bg-rose-400/16",
};

export function IncidentsTable({
  incidents,
  feedNameById,
}: {
  incidents: IncidentRecord[];
  feedNameById?: Record<string, string>;
}) {
  const { data: liveIncidents, setData: setLiveIncidents } = useLiveQuery({
    initialData: incidents,
    query: getIncidentsLive,
  });
  const [pendingIncidentId, setPendingIncidentId] = useState<string | null>(null);

  useEffect(() => {
    setLiveIncidents(incidents);
  }, [incidents, setLiveIncidents]);

  const columns = useMemo<ColumnDef<IncidentRecord>[]>(
    () => [
      {
        accessorKey: "id",
        header: "Incident",
        cell: ({ row }) => (
          <div>
            <div className="font-medium text-cyan-100">{row.original.id}</div>
            <Link
              href={`/feeds/${row.original.feed_id}`}
              className="mt-1 inline-block text-xs text-cyan-200/70 hover:text-cyan-100"
            >
              {feedNameById?.[row.original.feed_id] ?? row.original.feed_id}
            </Link>
          </div>
        ),
      },
      {
        accessorKey: "title",
        header: "Summary",
        cell: ({ row }) => (
          <div>
            <div>{row.original.title}</div>
            <div className="mt-1 text-xs text-white/50">{row.original.summary}</div>
          </div>
        ),
      },
      {
        accessorKey: "severity",
        header: "Severity",
        cell: ({ row }) => (
          <span
            className={`rounded-full px-2.5 py-1 text-xs font-medium uppercase tracking-[0.18em] ${
              severityClass[row.original.severity]
            }`}
          >
            {row.original.severity}
          </span>
        ),
      },
      {
        accessorKey: "status",
        header: "Workflow",
        cell: ({ row }) => (
          <div>
            <div className="uppercase tracking-[0.18em] text-white/80">
              {row.original.status}
            </div>
            <div className="mt-1 text-xs text-white/45">
              {row.original.acknowledged ? "Acknowledged" : "Needs acknowledgment"}
            </div>
          </div>
        ),
      },
      {
        accessorKey: "impacted_features",
        header: "Impacted Signals",
        cell: ({ row }) => (
          <div className="flex flex-wrap gap-2">
            {row.original.impacted_features.map((feature) => (
              <span
                key={feature}
                className="rounded-full bg-white/6 px-2.5 py-1 text-xs text-white/75"
              >
                {feature}
              </span>
            ))}
          </div>
        ),
      },
      {
        id: "actions",
        header: "Action",
        cell: ({ row }) =>
          row.original.acknowledged ? (
            <Link
              href="/incidents"
              className="inline-flex rounded-full border border-cyan-300/20 px-3 py-1 text-xs uppercase tracking-[0.18em] text-cyan-100 hover:bg-cyan-400/10"
            >
              Replay
            </Link>
          ) : (
            <button
              type="button"
              disabled={pendingIncidentId === row.original.id}
              onClick={async () => {
                const incidentId = row.original.id;
                const previousIncidents = liveIncidents;
                setPendingIncidentId(incidentId);
                setLiveIncidents(
                  liveIncidents.map((incident) =>
                    incident.id === incidentId
                      ? { ...incident, acknowledged: true, status: "investigating" as const }
                      : incident
                  )
                );

                const updatedIncident = await acknowledgeIncident(incidentId);

                if (updatedIncident) {
                  setLiveIncidents(
                    previousIncidents.map((incident) =>
                      incident.id === incidentId ? updatedIncident : incident
                    )
                  );
                } else {
                  setLiveIncidents(previousIncidents);
                }

                setPendingIncidentId(null);
              }}
              className="inline-flex rounded-full border border-orange-300/25 px-3 py-1 text-xs uppercase tracking-[0.18em] text-orange-100 transition-colors hover:bg-orange-300/12 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Acknowledge
            </button>
        ),
      },
    ],
    [feedNameById, liveIncidents, pendingIncidentId, setLiveIncidents]
  );

  // TanStack Table is intentionally used here for the operations grid.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data: liveIncidents,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="overflow-hidden rounded-xl panel">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-white/3 text-xs uppercase tracking-[0.24em] text-white/45">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} className="px-4 py-3 font-medium">
                  {flexRender(
                    header.column.columnDef.header,
                    header.getContext()
                  )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              className="border-t border-white/6 transition-colors hover:bg-white/3"
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-4 text-white/75">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
