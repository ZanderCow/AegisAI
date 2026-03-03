/**
 * Defines the configuration for a single column in the DataTable.
 * @template T - The type of data represented by each row.
 */
interface Column<T> {
  /** A unique identifier for the column. */
  key: string;

  /** The text displayed in the column header. */
  header: string;

  /** A function that returns the React node to render for a given item in this column. */
  render: (item: T) => React.ReactNode;

  /** Optional additional Tailwind classes for the table data cells in this column. */
  className?: string;
}

/**
 * Props for the DataTable component.
 * @template T - The type of data represented by each row.
 */
interface DataTableProps<T> {
  /** An array of column configurations. */
  columns: Column<T>[];

  /** The array of data items to display in the table. */
  data: T[];

  /** A function that extracts a unique key string from a data item, used for React list keys. */
  keyExtractor: (item: T) => string;

  /** 
   * The message to display when the data array is empty. 
   * @default 'No data found'
   */
  emptyMessage?: string;
}

/**
 * Renders a data table with typed columns and rows.
 * Supports custom rendering per column and an empty state message.
 *
 * @template T - The type of data represented by each row.
 * @param props - The DataTable properties.
 * @returns The rendered DataTable component.
 */
export function DataTable<T>({ columns, data, keyExtractor, emptyMessage = 'No data found' }: DataTableProps<T>) {
  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-800">
        <thead className="bg-gray-800/50">
          <tr>
            {columns.map(col => (
              <th
                key={col.key}
                className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {data.map(item => (
            <tr key={keyExtractor(item)} className="hover:bg-gray-800/50">
              {columns.map(col => (
                <td key={col.key} className={col.className || 'px-4 py-3 text-sm text-gray-300 whitespace-nowrap'}>
                  {col.render(item)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
