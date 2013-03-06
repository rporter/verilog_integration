.PHONY : clean deepclean

mdb.db : create.sqlite
	test -e $@ || sqlite3 $@ < $<

clean :

deepclean :
	rm *.db
