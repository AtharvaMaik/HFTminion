"use client";

import { useEffect, useRef, useState } from "react";

type UseLiveQueryOptions<T> = {
  initialData: T;
  intervalMs?: number;
  query: () => Promise<T>;
};

export function useLiveQuery<T>({
  initialData,
  intervalMs = 5000,
  query,
}: UseLiveQueryOptions<T>) {
  const [data, setData] = useState(initialData);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const mountedRef = useRef(true);
  const queryRef = useRef(query);

  queryRef.current = query;

  useEffect(() => {
    setData(initialData);
  }, [initialData]);

  useEffect(() => {
    mountedRef.current = true;

    const refresh = async () => {
      setIsRefreshing(true);
      try {
        const nextData = await queryRef.current();
        if (mountedRef.current) {
          setData(nextData);
        }
      } finally {
        if (mountedRef.current) {
          setIsRefreshing(false);
        }
      }
    };

    const intervalId = window.setInterval(() => {
      void refresh();
    }, intervalMs);
    void refresh();

    return () => {
      mountedRef.current = false;
      window.clearInterval(intervalId);
    };
  }, [intervalMs]);

  return { data, isRefreshing, setData };
}
