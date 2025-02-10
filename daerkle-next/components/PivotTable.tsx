'use client';

import { Table, TableHead, TableRow, TableHeaderCell, TableBody, TableCell, Badge } from '@tremor/react';
import useSWR from 'swr';

interface PivotTableProps {
  symbol: string;
  timeframe: string;
}

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function PivotTable({ symbol, timeframe }: PivotTableProps) {
  const { data, error, isLoading } = useSWR(
    `/api/pivot-levels?symbol=${symbol}&timeframe=${timeframe}`,
    fetcher
  );

  if (error) return <div>Failed to load pivot data</div>;
  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Pivot Levels</h3>
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Level</TableHeaderCell>
            <TableHeaderCell>Standard</TableHeaderCell>
            <TableHeaderCell>DeMark</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data?.levels.map((level: any) => (
            <TableRow key={level.name}>
              <TableCell>{level.name}</TableCell>
              <TableCell>{level.standard.toFixed(2)}</TableCell>
              <TableCell>{level.demark?.toFixed(2) || '-'}</TableCell>
              <TableCell>
                <Badge
                  color={level.status === 'active' ? 'green' : 'gray'}
                >
                  {level.status}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {data?.setups && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-4">DeMark Setups</h3>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(data.setups).map(([type, setup]: [string, any]) => (
              <div key={type} className="p-4 border rounded-lg">
                <h4 className="font-medium capitalize">{type} Setup</h4>
                <p className="mt-2">
                  Status: <Badge color={setup.active ? 'green' : 'gray'}>
                    {setup.active ? 'Active' : 'Inactive'}
                  </Badge>
                </p>
                {setup.count > 0 && (
                  <p className="mt-1">Count: {setup.count}/9</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
