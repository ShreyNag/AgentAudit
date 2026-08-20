import { useQuery } from "@tanstack/react-query";

import { providersService } from "@/api/services/providers";

export function useProviderList() {
  return useQuery({
    queryKey: ["providers", "list"],
    queryFn: () => providersService.list(),
    staleTime: Infinity, // the registered provider set never changes at runtime
  });
}

export function useProviderHealth() {
  return useQuery({
    queryKey: ["provider-health"],
    queryFn: () => providersService.health(),
    retry: false,
  });
}
