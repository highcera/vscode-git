$(document).ready(function () {

    savExchApi();

    let exchList = [];
    let countryList = [];

    // 환율 계산기 버튼 클릭 시, API 호출
    $("#exchBtn, #tripCalBtn").on("click", function(){
        getExchApiList(this);
    });

    //
    $("#addRowBtn").on("click", function(){
        let $table = $("#travelTable");
        let $tbody = $table.find("tbody");
        let $tr = $tbody.find("tr:last").clone(true);
        $tbody.append($tr);
    });

    //
    $("input[name=money]").on("click", function(){
        let total=0;

        let $tbody = $table.find("tbody");
        let $tr = $tbody.find("tr:last").clone(true);
        $tbody.append($tr);
    });

    const savExchApi = () => {
        return new Promise((resolove, reject) => {
            $.ajax({
                url: '/project/savExchApi.do',
                type: 'GET',
                data: { date: '20250415' },
                success: (response) => {
                    console.log(response);
                },
                error: (xhr, status, error) => {
                    console.error("에러 발생:", error);
                    reject(error);
                }

            });
        });
    }
})