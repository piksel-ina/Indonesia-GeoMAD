.PHONY : start rm exec save-tasks

start: 
	docker compose up -d geomad

rm:
	docker compose down geomad

exec:
	docker compose exec -it geomad bash

save-tasks:
	docker compose exec -it geomad \
		odc-stats save-tasks \
		    --frequency "annual" \
		    --grid "EPSG:6933;10;5000" \
		    --year "2024" \
		    --input-products "s2_l2a" \
		    --dataset-filter='{"cloud_cover": [0,60]}' \
		    job.db
