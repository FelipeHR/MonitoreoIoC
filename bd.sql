CREATE TABLE Host(
    IP varchar(20) PRIMARY KEY NOT NULL,
    MAC varchar(20) NOT NULL
);
CREATE TABLE Reporte(
    Id_reporte INTEGER PRIMARY KEY NOT NULL AUTO_INCREMENT,
    Fecha date NOT NULL,
    Hora timestamp NOT NULL,
    Datos JSON NOT NULL
);
CREATE TABLE Host_Reporte(
    IP varchar(20) REFERENCES Host(IP),
    Id_reporte INTEGER REFERENCES Reporte(Id_reporte),
    PRIMARY KEY(IP, Id_reporte)
); 
