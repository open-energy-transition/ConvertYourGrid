[out:xml][timeout:500];

// Get the complete administrative boundary relation and its members
relation["boundary"~"administrative|disputed"]["admin_level"="2"]["ISO3166-1:alpha2"="MM"]->.admin_boundary;
(.admin_boundary; >;);
// Convert the full relation into an area, which we use for the subsequent search
.admin_boundary map_to_area ->.searchArea;

way(area.searchArea)[~"^(construction:|disused:)?power$"~"^line|cable$"] -> .segments;

// Dependencies gathering
(
.segments;
);
(._;>;);

out meta;