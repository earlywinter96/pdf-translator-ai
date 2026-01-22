import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
    },
    sitemap: "https://pdf-translator-ai-xgu2.vercel.app/sitemap.xml",
  };
}
