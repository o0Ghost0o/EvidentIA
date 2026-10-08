/** Client-side pagination over an already-filtered/sorted array. Slices the source
 * into pages, clamps the current page when the source shrinks, and resets to page 1
 * whenever the source length changes (e.g. after a filter or search). */
import { computed, ref, watch, type ComputedRef, type Ref } from "vue";

export interface UsePaginationOptions {
  /** Rows per page. Defaults to 10. */
  pageSize?: number;
}

export function usePagination<T>(
  source: Ref<T[]> | ComputedRef<T[]>,
  options: UsePaginationOptions = {}
) {
  const pageSize = ref(options.pageSize ?? 10);
  const page = ref(1);

  const total = computed(() => source.value?.length ?? 0);
  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)));

  function setPage(p: number) {
    page.value = Math.min(Math.max(1, Math.trunc(p)), pageCount.value);
  }
  function next() {
    setPage(page.value + 1);
  }
  function prev() {
    setPage(page.value - 1);
  }

  // Reset to the first page whenever the source array is recomputed (filter / search /
  // sort / reload all produce a new array), and clamp when the page count shrinks.
  watch(
    () => source.value,
    () => {
      page.value = 1;
    }
  );
  watch(pageSize, () => setPage(page.value));

  const rangeStart = computed(() => (total.value === 0 ? 0 : (page.value - 1) * pageSize.value + 1));
  const rangeEnd = computed(() => Math.min(page.value * pageSize.value, total.value));

  const paged = computed<T[]>(() => {
    const start = (page.value - 1) * pageSize.value;
    return (source.value ?? []).slice(start, start + pageSize.value);
  });

  return { page, pageSize, total, pageCount, rangeStart, rangeEnd, paged, setPage, next, prev };
}
