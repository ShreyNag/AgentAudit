import { useQuery } from "@tanstack/react-query";

import { providersService } from "@/api/services/providers";

export function useProviderHealth() {
  return useQuery({
    queryKey: ["provider-health"],
    queryFn: () => providersService.health(),
    retry: false,
  });
}
