.PHONY : clean deepclean

mdb.db : create.sqlite
	sqlite3 $@ < $<

clean :

deepclean :
	rm *.db
