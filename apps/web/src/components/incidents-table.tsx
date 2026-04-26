"use client";

import type { IncidentRecord } from "@contracts";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import { useMemo } from "react";

const severityClass = {
  healthy: "text-emerald-200 bg-emerald-400/12",
  warning: "text-orange-100 bg-orange-300/14",
  critical: "text-rose-100 bg-rose-400/16",
};

export function IncidentsTable({ incidents }: { incidents: IncidentRecord[] }) {
  const columns = useMemo<ColumnDef<IncidentRecord>[]>(
    () => [
      { accessorKey: "id", header: "Incident" },
      { accessorKey: "title", header: "Summary" },
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
      { accessorKey: "status", header: "Workflow" },
      {
        accessorKey: "impacted_features",
        header: "Impacted Features",
        cell: ({ row }) => row.original.impacted_features.join(", "),
      },
    ],
    []
  );

  // TanStack Table is intentionally used here for the operations grid.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data: incidents,
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
