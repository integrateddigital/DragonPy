1 PRINT:PRINT "TEST CC REGISTERS V0.1"
2 PRINT "(GPL V3 OR ABOVE)"
3 PRINT:PRINT "COPYLEFT (C) 2013 JENS DIEMER":PRINT
11 COUNT=14
20 LA=&H4000			' LOAD / EXECUTE ADDRESS
25 PRINT "POKE MACHINE CODE TO: $";HEX$(LA)
30 PA = LA			' START ADDRESS FOR POKE
50 READ HB$			' HEX CONSTANTS
60 IF HB$="END" THEN 100
65 V=VAL("&H"+HB$)
70 POKE PA,V	                ' POKE VALUE INTO MEMORY
75 'PRINT "POKE $";HEX$(V);" AT $";HEX$(PA)
80 PA = PA + 1			' INCREMENT POKE ADDRESS
90 GOTO 50
100 PRINT "LOADED, END ADDRESS IS: $"; HEX$(PA-1)
110 PRINT:INPUT "INPUT START VALUE (DEZ)";A$
115 IF A$="" THEN 20000 ELSE A=VAL(A$)
120 A=A-1
130 GOTO 500
140 PRINT "UP/DOWN OR ANYKEY FOR NEW VALUE";
150 I$ = INKEY$:IF I$="" THEN 150
160 IF I$=CHR$(&H5E) THEN A=A-(COUNT*2):GOTO 500 ' UP KEYPRESS
170 IF I$=CHR$(&H0A) THEN 500 ' DOWN KEYPRESS
180 GOTO 110 ' NOT UP/DOWN
500 A=A AND &HFF ' WRAP AROUND
510 POKE &H4500,A ' SET START VALUE
520 'PRINT "A=";A;" VALUE FROM $4500: ";PEEK(&H4500)
540 PRINT @ 0, "             EFHINZVC"
550 FOR I = 1 TO COUNT
560 EXEC LA
570 CC=PEEK(&H4501) ' CC-REGISTER
580 A=PEEK(&H4500) ' ACCU A
590 ' CREATE BITS
600 T = CC
610 B7$="0":IF T AND 128 THEN B7$="1"
620 B6$="0":IF T AND 64 THEN B6$="1"
630 B5$="0":IF T AND 32 THEN B5$="1"
640 B4$="0":IF T AND 16 THEN B4$="1"
650 B3$="0":IF T AND 8 THEN B3$="1"
660 B2$="0":IF T AND 4 THEN B2$="1"
670 B1$="0":IF T AND 2 THEN B1$="1"
680 B0$="0":IF T AND 1 THEN B1$="1"
690 PRINT "A=";RIGHT$("  "+STR$(A),3);" CC=$";HEX$(CC);":";B7$;B6$;B5$;B4$;B3$;B2$;B1$;B0$
700 NEXT I
710 GOTO 140
1000 ' MACHINE CODE IN HEX
1009 ' LDA $4500
1010 DATA B6,45,00
1019 ' ADDA 1
1020 DATA 8B,01
1029 ' TFR CC,B
1030 DATA 1F,A9
1039 ' STD $4500 ; STORE A+B
1040 DATA FD,45,00
1049 ' RTS
1050 DATA 39
10000 DATA END
20000 PRINT:PRINT "BYE"
