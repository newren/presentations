.PHONY: clean slides handouts all tag
BASE=merge-performance
SLIDES_PDF=$(BASE)-slides.pdf
HANDOUTS_PDF=$(BASE)-handout.pdf

#TEXMF_PATHS=$(shell ./texmf-paths.sh)
#PDFLATEX=TEXINPUTS=.:$(TEXMF_PATHS): pdflatex -halt-on-error
PDFLATEX=pdflatex -halt-on-error

UNAME:=$(shell uname)
MAC_READER=open
PDF_READER:=$(shell if test $(UNAME) = Linux; then echo evince ; else echo $(MAC_READER); fi)

OTHER_FILES=\
	#gitk-jgit-screenshot.png \
	#gitk-view-screenshot.png \
	preamble.tex

all: slides handouts

slides: $(SLIDES_PDF)

handouts: $(HANDOUTS_PDF)

$(SLIDES_PDF): $(BASE).tex $(OTHER_FILES)
	$(PDFLATEX) -jobname merge-performance-slides "\def\slides{}\input{"$(BASE).tex"}"
	$(PDFLATEX) -jobname merge-performance-slides "\def\slides{}\input{"$(BASE).tex"}"

$(HANDOUTS_PDF): $(BASE).tex $(OTHER_FILES)
	$(PDFLATEX) -jobname merge-performance-handout "\def\handout{}\input{"$(BASE).tex"}"
	$(PDFLATEX) -jobname merge-performance-handout "\def\handout{}\input{"$(BASE).tex"}"

clean:
	rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb *~ .*~ $(SLIDES_PDF) $(HANDOUTS_PDF)
