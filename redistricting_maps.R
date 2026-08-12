install.packages("sf")
install.packages("sp")
install.packages("fastmap")
install.packages("ggplot2")
install.packages("raster")
install.packages("base")
install.packages("dplyr")
install.packages("httr")

### installing packages

library(sp)
library(fastmap)
library(sf)
library(ggplot2)
library(raster)
library(base)
library(dplyr)
library(httr)


setwd("~/Documents/Current Projects/Sett Col/R/Rshapefiles")

### To make other maps you need to convert ward polygons to lines in pro,
###  then merge the lines,
###  export
###  input to R

  
  ##### CHICAGO POST 1923 #####################################################
### installing shapefile and creating data frames

terrm <- st_read("~/Documents/Current Projects/Sett Col/R/Rshapefiles/terrm.shp")
wards15 <- st_read("~/Documents/Current Projects/Sett Col/R/Rshapefiles/CHI_2015.shp")
cwardline <- st_read("~/Documents/Current Projects/Sett Col/R/Rshapefiles/chiward15line.shp")

geom <- terrm$geometry
Year <- as.numeric(terrm$terrm_csv1) ### convert string to numeric
Hexagons <- as.numeric(terrm$terrm_csv1) ### convert string to numeric
data <- data.frame(terrm)
wgeom <- wards15$geometry
wards <- cbind(wards15, st_coordinates(st_centroid(wards15)))
wardlinegeom <- cwardline$geometry

cplot <- ggplot() +
  geom_sf(data = geom, aes(fill = Hexagons), color = NA) +
  scale_fill_viridis_b(option = "viridis",
                       breaks = c(1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                       labels = c("Core Community", "In Ward Since 1931", "In Ward Since 1947", "In Ward Since 1961", "In Ward Since 1970", "In Ward Since 1981", "In Ward Since 1985", "In Ward Since 1995", "In Ward Since 2005", "In Ward Since 2015")) +
  geom_sf(data = wardlinegeom, aes(color = "Black")) +
  scale_color_identity(name = NULL,
                       breaks = c("Black"),
                       labels = c("2015 Ward Boundaries"),
                       guide = "legend") +
  geom_text(data = wards, aes(X, Y, label = wards15$ward2015), color = "Black", size = 4) +
  guides(fill = guide_colourbar(barwidth = 1, barheight = 10)) +
  theme(legend.text = element_text(size=12)) +
  theme_void()

###exporting Chicago map to high res pdf

cplot2 <- cplot

setwd("~/Downloads")
cplot2
ggsave("chiterr1923.pdf", cplot2, width = 8, height = 11, dpi = 1000)

### PRE 1923 CHICAGO VIS ###############################################
### installing shapefiles and creating data frames
terr18 <- st_read("~/Downloads/terr18002.shp")
Chi1912L <- st_read("~/Downloads/Chi1912L.shp")
Chi1912W <- st_read("~/Downloads/CHI_1912.shp")

terr18 <- st_read("~/Documents/Current Projects/Sett Col/R/Rshapefiles/terr18002.shp")
Chi1912L <- st_read("~/Documents/Current Projects/Sett Col/R/Rshapefiles/Chi1912L.shp")
Chi1912W <- st_read("~/Documents/Current Projects/Sett Col/R/Rshapefiles/CHI_1912.shp")


t18geom <- terr18$geometry
Year <- as.numeric(terr18$Chicago_23)
Hexagons <- as.numeric(terr18$Chicago_23)
wgeom <- Chi1912W$geometry
wards <- cbind(Chi1912W, st_coordinates(st_centroid(Chi1912W)))
wardlinegeom <- Chi1912L$geometry

### PLOT
cplot18 <- ggplot() +
  geom_sf(data = t18geom, aes(fill = Hexagons), color = NA) +
  scale_fill_viridis_b(option = "viridis",
                       breaks = c(1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                       labels = c("Core Community", "In Ward Since 1847", "In Ward Since 1857", "In Ward Since 1863", "In Ward Since 1869", "In Ward Since 1876", "In Ward Since 1890", "In Ward Since 1900", "In Ward Since 1910", "In Ward Since 1912")) +
  geom_sf(data = wardlinegeom, aes(color = "Black")) +
  scale_color_identity(name = NULL,
                       breaks = c("Black"),
                       labels = c("1912 Ward Boundaries"),
                       guide = "legend") +
  geom_text(data = wards, aes(X, Y, label = ward1912), color = "Black", face = "bold", size = 4) +
  theme_void() +
  theme (legend.text=element_text(size=12)) +
  guides(fill = guide_colourbar(barwidth = 1, barheight = 12))

chisetts <- st_read("~/Documents/Current Projects/Sett Col/R/Rshapefiles/Annexed Settlements.shp")

setwd("~/Downloads")
cplot18
ggsave("chiterr18.pdf", cplot18, width = 8, height = 11, dpi = 1000)


####################################################################
##### St Louis pre1876
stlterr <- st_read("/Users/robertvargas/Documents/Research/Current Projects/Stability Paper/R/Rshapefiles/STL Emergence1830.shp")
STL18L <- st_read("/Users/robertvargas/Documents/Research/Current Projects/Stability Paper/R/Rshapefiles/STL1875L.shp")
STL1875W <- st_read("/Users/robertvargas/Documents/Research/Current Projects/Stability Paper/R/Rshapefiles/1875_STL2.shp")

stlgeom <- stlterr$geometry
Year <- as.numeric(stlterr$terr1830)
Hexagons <- as.numeric(stlterr$terr1830)
wgeom <- STL1875W$geometry
wards <- cbind(STL1875W, st_coordinates(st_centroid(STL1875W)))
wardlinegeom <- STL18L$geometry

stlplot <- ggplot() +
  geom_sf(data = stlgeom, aes(fill = Hexagons), color = NA) +
  scale_fill_viridis_b(option = "magma",
                       breaks = c(1, 2, 3, 4, 5),
                       labels = c("Core Community", "In Ward Since 1855", "In Ward Since 1856", "In Ward Since 1867", "In Ward Since 1870")) +
  geom_sf(data = wardlinegeom, aes(color = "Black")) +
  scale_color_identity(name = NULL,
                       breaks = c("Black"),
                       labels = c("1874 Ward Boundaries"),
                       guide = "legend") +
  geom_text(data = wards, aes(X, Y, label = ward1875), color = "Black", size = 4) +
  theme_void() +
  theme (legend.text=element_text(size=12)) +
  guides(fill = guide_colourbar(barwidth = 1, barheight = 10))

#### Export High Res Photo

setwd("~/Downloads")
stlplot
ggsave("stlterr1830.tiff", stlplot, width = 8, height = 11, dpi = 1000)




####### STL Terr 1876 to Present###########################################################
###########################################################################################
###########################################################################################
stlterr <- st_read("/Users/robertvargas/Documents/Research/Current Projects/Stability Paper/R/Rshapefiles/STL Emergence Analysis.shp")
STL2011L <- st_read("/Users/robertvargas/Documents/Research/Current Projects/Stability Paper/R/Rshapefiles/STL2011L.shp")
STL2011W <- st_read("/Users/robertvargas/Documents/Research/Current Projects/Stability Paper/R/Rshapefiles/2011_STL2.shp")

stlgeom <- stlterr$geometry
Hexagons <- as.numeric(stlterr$terr1876)
Year <- as.numeric(stlterr$terr1876)
wgeom <- STL2011W$geometry
wards <- cbind(STL2011W, st_coordinates(st_centroid(STL2011W)))
wardlinegeom <- STL2011L$geometry

stlplot <- ggplot() +
  geom_sf(data = stlgeom, aes(fill = Year), color = NA) +
  scale_fill_viridis_b(option = "magma",
                       breaks = c(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13),
                       labels = c("Core Community", "In Ward Since 1898", "In Ward Since 1909", "In Ward Since 1921", "In Ward Since 1943", "In Ward Since 1965", "In Ward Since 1966", "In Ward Since 1971", "In Ward Since 1978", "In Ward Since 1982", "In Ward Since 1991", "In Ward Since 2001", "In Ward Since 2011")) +
  geom_sf(data = wardlinegeom, aes(color = "Black")) +
  scale_color_identity(name = NULL,
                       breaks = c("Black"),
                       labels = c("2011 Ward Boundaries"),
                       guide = "legend") +
  geom_text(data = wards, aes(X, Y, label = ward2011), color = "Black", size = 4) +
  theme_void() +
  theme (legend.text=element_text(size=12)) +
  guides(fill = guide_colourbar(barwidth = 1, barheight = 10))

### Export post 1876 STL map to tiff

setwd("~/Downloads")
stlplot
ggsave("stlterr1876.tiff", stlplot, width = 8, height = 11, dpi = 1000)



###### Milwaukee territorialization##########################################################
#############################################################################################
#############################################################################################
#############################################################################################
milterr <- st_read("~/Documents/Current Projects/Sett Col/R/Rshapefiles/MIL Emergence2.shp")
mwards <- st_read("~/Documents/Current Projects/Sett Col/R/Rshapefiles/MIL_2011.shp")
mwardl <- st_read("~/Documents/Current Projects/Sett Col/R/Rshapefiles/MILL.shp")

mil_geom <- milterr$geometry
Year <- as.numeric(milterr$terr)
Hexagons <- as.numeric(milterr$terr)
mgeom <- mwards$geometry
wards <- cbind(mwards, st_coordinates(st_centroid(mwards)))
wardlinegeom <- mwardl$geometry

tplot <- ggplot() +
  geom_sf(data = mil_geom, aes(fill = Hexagons), color = NA) +
  scale_fill_viridis_b(option = "cividis",
                       breaks = c(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13),
                       labels = c("Core Community", "In Ward Since 1856", "In Ward Since 1873", "In Ward Since 1874", "In Ward Since 1911", "In Ward Since 1931", "In Ward Since 1956", "In Ward Since 1963", "In Ward Since 1972", "In Ward Since 1982", "In Ward Since 1991", "In Ward Since 2004", "In Ward Since 2011")) +
  geom_sf(data = wardlinegeom, aes(color = "Black")) +
  scale_color_identity(name = NULL,
                       breaks = c("Black"),
                       labels = c("2011 Ward Boundaries"),
                       guide = "legend") +
  geom_text(data = wards, aes(X, Y, label = ward2011), color = "Black", size = 3) +
  theme_void() +
  guides(fill = guide_colourbar(barwidth = 1, barheight = 12))+
  theme(legend.text = element_text(size=12))

### Export High Res Photo

setwd("~/Downloads")
tplot
ggsave("milterr.tiff", tplot, width = 8, height = 11, dpi = 1000)







*** art ***
  
  ggplot() +
  geom_sf(data = geom, aes(fill = Hexagons), color = NA) +
  scale_fill_viridis_b(option = "viridis",
                       breaks = c(1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                       labels = c("Core Community", "In Ward Since 1931", "In Ward Since 1947", "In Ward Since 1961", "In Ward Since 1970", "In Ward Since 1981", "In Ward Since 1985", "In Ward Since 1995", "In Ward Since 2005", "In Ward Since 2015")) +
  scale_color_identity(name = NULL,
                       breaks = c("Black"),
                       labels = c("2015 Ward Boundaries"),
                       guide = "legend") +
  theme_void()