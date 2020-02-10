.PHONY: summit-topics.pdf it

summit-topics.pdf: summit-topics.tex
	@make clean
	pdflatex -halt-on-error $<
	#pdflatex -halt-on-error $<   # If run twice, TOC and quick-overviews exist

it: summit-topics.pdf
	pdflatex -halt-on-error summit-topics.tex

clean:
	rm -f *.aux *.log *.nav *.out *.snm *.toc
