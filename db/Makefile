.PHONY : clean deepclean

mdb.db : create.sqlite create.fcvg.sqlite
	test -e $@ || (cat $^ | sqlite3 $@)

clean :
	rm *.db

deepclean : clean
