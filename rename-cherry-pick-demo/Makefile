.PHONY: lots-o-renames.pdf it

lots-o-renames.pdf: lots-o-renames.tex
	@make clean
	pdflatex -halt-on-error $<
	#pdflatex -halt-on-error $<   # If run twice, TOC and quick-overviews exist

it: lots-o-renames.pdf
	pdflatex -halt-on-error lots-o-renames.tex

clean:
	rm -f *.aux *.log *.nav *.out *.snm *.toc
