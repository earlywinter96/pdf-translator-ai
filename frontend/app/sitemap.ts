import { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: "https://YOUR_DOMAIN.com",
      lastModified: new Date(),
    },
    {
      url: "https://YOUR_DOMAIN.com/convert",
      lastModified: new Date(),
    },
    {
      url: "https://YOUR_DOMAIN.com/privacy",
      lastModified: new Date(),
    },
    {
      url: "https://YOUR_DOMAIN.com/terms",
      lastModified: new Date(),
    },
  ];
}
